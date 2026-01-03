"""
Example configuration file for database connection
Copy this to config.py and modify as needed
"""
import os

# Database type: 'sqlite' or 'firebase'
DB_TYPE = os.getenv('DB_TYPE', 'sqlite')  # Default to SQLite

# SQLite configuration (local)
SQLITE_DB_NAME = os.getenv('SQLITE_DB_NAME', 'secure_email.db')

# Firebase configuration (cloud)
# To use Firebase:
# 1. Create a Firebase project at https://console.firebase.google.com/
# 2. Enable Firestore Database
# 3. Go to Project Settings → Service Accounts
# 4. Generate new private key and download JSON file
# 5. Set the path below or use environment variable:
#    export FIREBASE_CREDENTIALS_PATH=/path/to/service-account-key.json

FIREBASE_CONFIG = {
    'credentials_path': os.getenv('FIREBASE_CREDENTIALS_PATH', ''),
    'project_id': os.getenv('FIREBASE_PROJECT_ID', ''),
}

