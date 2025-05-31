# services/firebase_service.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

FIREBASE_URL = os.getenv("FIREBASE_DB_URL")

def update_firebase(public_url):
    """Update the public ngrok URL in Firebase."""
    data = {'url': public_url}
    response = requests.patch(FIREBASE_URL, json=data)
    if response.status_code == 200:
        print("Firebase URL updated successfully!")
        print(f" * Ngrok tunnel running at: {public_url}")

    else:
        print(f"Failed to update Firebase URL: {response.text}")