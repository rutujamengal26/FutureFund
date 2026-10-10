import os
import sys
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def test_alice_bob():
    print("Testing Alice and Bob isolation...")
    alice_email = f"alice_{datetime.now().timestamp()}@test.com"
    bob_email = f"bob_{datetime.now().timestamp()}@test.com"

    # Register Alice
    r = requests.post(f"{BASE_URL}/auth/register", json={
        "email": alice_email,
        "password": "password",
        "full_name": "Alice"
    })
    r.raise_for_status()

    # Login Alice
    r = requests.post(f"{BASE_URL}/auth/login", data={
        "username": alice_email,
        "password": "password"
    })
    r.raise_for_status()
    alice_token = r.json()["access_token"]
    alice_headers = {"Authorization": f"Bearer {alice_token}"}

    # Alice Profile
    profile_data = {
        "profile_name": "Alice Profile",
        "profile_data": {
            "monthly_income_inr": 50000,
            "monthly_rent_inr": 10000,
            "essential_expenses_excluding_rent_inr": 5000,
            "variable_expenses_inr": 5000,
            "current_savings_inr": 100000,
            "existing_monthly_emi_inr": 0,
            "other_income_inr": 0
        },
        "is_default": True
    }
    r = requests.post(f"{BASE_URL}/profiles", json=profile_data, headers=alice_headers)
    r.raise_for_status()
    alice_profile_id = r.json()["id"]

    # Register Bob
    r = requests.post(f"{BASE_URL}/auth/register", json={
        "email": bob_email,
        "password": "password",
        "full_name": "Bob"
    })
    r.raise_for_status()

    # Login Bob
    r = requests.post(f"{BASE_URL}/auth/login", data={
        "username": bob_email,
        "password": "password"
    })
    r.raise_for_status()
    bob_token = r.json()["access_token"]
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    # Bob tries to access Alice's profile
    r = requests.get(f"{BASE_URL}/profiles/{alice_profile_id}", headers=bob_headers)
    if r.status_code == 404:
        print("SUCCESS: Bob cannot access Alice's profile (404 expected).")
    else:
        print(f"FAILED: Bob received {r.status_code} when accessing Alice's profile.")
        sys.exit(1)
        
    print("Isolation test passed.")

if __name__ == "__main__":
    test_alice_bob()
