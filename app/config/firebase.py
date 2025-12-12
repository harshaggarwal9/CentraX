# config/firebase.py
import firebase_admin
from firebase_admin import credentials

def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate("firebase_key.json")

        firebase_admin.initialize_app(cred)
