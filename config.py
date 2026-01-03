"""
Configuration file for database connection
Supports SQLite (local) and Firebase Firestore (cloud)
"""
import os

# Database type: 'sqlite' or 'firebase'
DB_TYPE = os.getenv('DB_TYPE', 'sqlite')  # Default to SQLite

# SQLite configuration (local)
SQLITE_DB_NAME = os.getenv('SQLITE_DB_NAME', 'secure_email.db')

# Firebase configuration (cloud)
# To use Firebase, you need to:
# 1. Create a Firebase project at https://console.firebase.google.com/
# 2. Enable Firestore Database
# 3. Download service account key JSON file
# 4. Set FIREBASE_CREDENTIALS_PATH environment variable to the JSON file path
# 5. Set DB_TYPE=firebase

FIREBASE_CONFIG = {
    'credentials_path': os.getenv('FIREBASE_CREDENTIALS_PATH', ''),
    'project_id': os.getenv('FIREBASE_PROJECT_ID', ''),
}
