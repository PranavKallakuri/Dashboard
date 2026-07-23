"""
pull_transactions.py
---------------------
Connects to YOUR real bank account via GoCardless's Bank Account Data
API (UK Open Banking) and saves your real transaction history to
data/raw_transactions.json.

Run this LOCALLY, not on any hosted service — it needs your own
credentials and it will open a real bank authentication flow.

Setup (one-time):
  1. Create a free account at https://bankaccountdata.gocardless.com
  2. Copy your secret_id and secret_key into a file called .env
     in the project root (see .env.example):
         GC_SECRET_ID=your-id-here
         GC_SECRET_KEY=your-key-here
  3. pip install -r requirements.txt
  4. python scripts/pull_transactions.py
"""

import os
import time
import json
import webbrowser
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://bankaccountdata.gocardless.com/api/v2"
SECRET_ID = os.environ["GC_SECRET_ID"]
SECRET_KEY = os.environ["GC_SECRET_KEY"]
REDIRECT_URL = "https://example.com/callback"  # any URL — we only need the ?ref= redirect to finish


def get_access_token() -> str:
    """Step 1: exchange your secret_id/secret_key for a short-lived access token."""
    resp = requests.post(
        f"{BASE_URL}/token/new/",
        json={"secret_id": SECRET_ID, "secret_key": SECRET_KEY},
    )
    resp.raise_for_status()
    return resp.json()["access"]


def find_institution(token: str, bank_search_term: str) -> str:
    """
    Step 2: look up your bank's institution ID.
    Example: bank_search_term="Monzo" or "Barclays" or "Revolut".
    Prints matches so you can pick the exact one if there are several.
    """
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/institutions/?country=gb", headers=headers)
    resp.raise_for_status()
    matches = [i for i in resp.json() if bank_search_term.lower() in i["name"].lower()]
    for m in matches:
        print(f"  {m['id']}  ->  {m['name']}")
    if not matches:
        raise SystemExit(f"No institution found matching '{bank_search_term}'. Try a different search term.")
    return matches[0]["id"]  # take the first match — check the printed list if it's wrong


def create_requisition(token: str, institution_id: str) -> dict:
    """Step 3: create an agreement + requisition, which gives you a real bank login link."""
    headers = {"Authorization": f"Bearer {token}"}

    agreement = requests.post(
        f"{BASE_URL}/agreements/enduser/",
        headers=headers,
        json={
            "institution_id": institution_id,
            "max_historical_days": 180,   # how far back to pull — 180 is a good default
            "access_valid_for_days": 90,
            "access_scope": ["balances", "details", "transactions"],
        },
    ).json()

    requisition = requests.post(
        f"{BASE_URL}/requisitions/",
        headers=headers,
        json={
            "redirect": REDIRECT_URL,
            "institution_id": institution_id,
            "agreement": agreement["id"],
        },
    ).json()

    return requisition


def wait_for_link(token: str, requisition_id: str) -> list:
    """Step 4: poll until you've completed the bank login in your browser."""
    headers = {"Authorization": f"Bearer {token}"}
    print("\nWaiting for you to complete the bank login in your browser...")
    while True:
        resp = requests.get(f"{BASE_URL}/requisitions/{requisition_id}/", headers=headers).json()
        if resp["status"] == "LN":  # linked
            return resp["accounts"]
        time.sleep(3)


def fetch_transactions(token: str, account_id: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/accounts/{account_id}/transactions/", headers=headers)
    resp.raise_for_status()
    return resp.json()


def main():
    print("Getting access token...")
    token = get_access_token()

    bank_name = input("Which bank do you want to connect? (e.g. Monzo, Barclays, Revolut): ")
    print(f"Searching institutions matching '{bank_name}'...")
    institution_id = find_institution(token, bank_name)

    print("Creating a secure link to your bank...")
    requisition = create_requisition(token, institution_id)
    print(f"\nOpen this link and log in to your real bank account:\n{requisition['link']}\n")
    webbrowser.open(requisition["link"])

    account_ids = wait_for_link(token, requisition["id"])
    print(f"Linked. Found {len(account_ids)} account(s).")

    all_transactions = []
    for acc_id in account_ids:
        data = fetch_transactions(token, acc_id)
        all_transactions.append({"account_id": acc_id, "transactions": data["transactions"]})

    os.makedirs("data", exist_ok=True)
    with open("data/raw_transactions.json", "w") as f:
        json.dump(all_transactions, f, indent=2)

    print("\nSaved real transactions to data/raw_transactions.json")
    print("This file contains real account details — it's already in .gitignore. Never commit it.")


if __name__ == "__main__":
    main()
