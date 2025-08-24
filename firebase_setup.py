import firebase_admin
from firebase_admin import credentials, firestore, auth
import logging

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def verify_firebase_token(id_token):
    """Verify Firebase ID token and return decoded claims"""
    try:
        # Verify the ID token and get decoded claims
        decoded_token = auth.verify_id_token(id_token)
        logging.info(f"Token verified for user: {decoded_token.get('email', 'unknown')}")
        return decoded_token
    except Exception as e:
        logging.error(f"Token verification failed: {e}")
        raise e