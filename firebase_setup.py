import firebase_admin
from firebase_admin import credentials, firestore
import logging

# Initialize Firebase Admin SDK only if not already initialized
try:
    # Check if default app already exists
    firebase_admin.get_app()
    logging.info("Firebase app already initialized")
except ValueError:
    # App doesn't exist, so initialize it
    try:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        logging.info("Firebase app initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize Firebase Admin SDK: {e}")
        raise

# Get Firestore client
db = firestore.client()