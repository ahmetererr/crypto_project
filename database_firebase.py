"""
Firebase Firestore database module for storing users, public keys, and messages
"""
from google.cloud import firestore
from typing import Optional, List, Tuple
import os
import json


class DatabaseFirebase:
    def __init__(self, credentials_path: str = None, project_id: str = None):
        """
        Initialize Firebase Firestore connection
        
        Args:
            credentials_path: Path to Firebase service account JSON file
            project_id: Firebase project ID (optional if in credentials)
        """
        if credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        try:
            if project_id:
                self.db = firestore.Client(project=project_id)
            else:
                self.db = firestore.Client()
            self.init_database()
        except Exception as e:
            raise Exception(f"Failed to connect to Firebase: {str(e)}. Make sure credentials are set correctly.")
    
    def init_database(self):
        """Initialize database collections (Firestore creates collections automatically)"""
        # Firestore doesn't need explicit table creation
        # Collections are created when first document is added
        pass
    
    def add_user(self, username: str, password_hash: str) -> bool:
        """Add a new user to the database"""
        try:
            users_ref = self.db.collection('users')
            # Check if user already exists
            user_doc = users_ref.document(username).get()
            if user_doc.exists:
                return False  # Username already exists
            
            users_ref.document(username).set({
                'username': username,
                'password_hash': password_hash,
                'created_at': firestore.SERVER_TIMESTAMP
            })
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False
    
    def get_user_password_hash(self, username: str) -> Optional[str]:
        """Get password hash for a user"""
        try:
            user_doc = self.db.collection('users').document(username).get()
            if user_doc.exists:
                return user_doc.to_dict().get('password_hash')
            return None
        except Exception as e:
            print(f"Error getting user password hash: {e}")
            return None
    
    def user_exists(self, username: str) -> bool:
        """Check if user exists"""
        try:
            user_doc = self.db.collection('users').document(username).get()
            return user_doc.exists
        except Exception as e:
            print(f"Error checking user existence: {e}")
            return False
    
    def save_public_key(self, username: str, public_key: str) -> bool:
        """Save user's public key"""
        try:
            self.db.collection('public_keys').document(username).set({
                'username': username,
                'public_key': public_key
            })
            return True
        except Exception as e:
            print(f"Error saving public key: {e}")
            return False
    
    def save_private_key(self, username: str, private_key: str) -> bool:
        """Save user's private key"""
        try:
            self.db.collection('private_keys').document(username).set({
                'username': username,
                'private_key': private_key
            })
            return True
        except Exception as e:
            print(f"Error saving private key: {e}")
            return False
    
    def get_public_key(self, username: str) -> Optional[str]:
        """Get user's public key"""
        try:
            key_doc = self.db.collection('public_keys').document(username).get()
            if key_doc.exists:
                return key_doc.to_dict().get('public_key')
            return None
        except Exception as e:
            print(f"Error getting public key: {e}")
            return None
    
    def get_private_key(self, username: str) -> Optional[str]:
        """Get user's private key"""
        try:
            key_doc = self.db.collection('private_keys').document(username).get()
            if key_doc.exists:
                return key_doc.to_dict().get('private_key')
            return None
        except Exception as e:
            print(f"Error getting private key: {e}")
            return None
    
    def save_message(self, sender: str, recipient: str, encrypted_content: str,
                     encrypted_symmetric_key: str, message_hash: str, digital_signature: str, 
                     subject: str = None) -> bool:
        """Save encrypted message"""
        try:
            messages_ref = self.db.collection('messages')
            messages_ref.add({
                'sender': sender,
                'recipient': recipient,
                'encrypted_content': encrypted_content,
                'encrypted_symmetric_key': encrypted_symmetric_key,
                'message_hash': message_hash,
                'digital_signature': digital_signature,
                'is_read': False,
                'subject': subject,
                'created_at': firestore.SERVER_TIMESTAMP
            })
            return True
        except Exception as e:
            print(f"Error saving message: {e}")
            return False
    
    def get_messages_for_user(self, username: str) -> List[Tuple]:
        """Get all messages for a user"""
        try:
            messages_ref = self.db.collection('messages')
            query = messages_ref.where('recipient', '==', username).order_by('created_at', direction=firestore.Query.DESCENDING)
            docs = query.stream()
            
            results = []
            for doc in docs:
                data = doc.to_dict()
                # Convert to tuple format compatible with SQLite version
                # (id, sender, recipient, encrypted_content, encrypted_symmetric_key, message_hash, digital_signature, is_read, subject, created_at)
                results.append((
                    doc.id,  # Firestore document ID
                    data.get('sender'),
                    data.get('recipient'),
                    data.get('encrypted_content'),
                    data.get('encrypted_symmetric_key'),
                    data.get('message_hash'),
                    data.get('digital_signature'),
                    data.get('is_read', False),
                    data.get('subject'),
                    data.get('created_at')
                ))
            return results
        except Exception as e:
            print(f"Error getting messages: {e}")
            return []
    
    def mark_as_read(self, message_id: str) -> bool:
        """Mark message as read"""
        try:
            self.db.collection('messages').document(message_id).update({
                'is_read': True
            })
            return True
        except Exception as e:
            print(f"Error marking message as read: {e}")
            return False
    
    def get_message_by_id(self, message_id: str) -> Optional[Tuple]:
        """Get message by ID"""
        try:
            doc = self.db.collection('messages').document(message_id).get()
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            return (
                doc.id,
                data.get('sender'),
                data.get('recipient'),
                data.get('encrypted_content'),
                data.get('encrypted_symmetric_key'),
                data.get('message_hash'),
                data.get('digital_signature'),
                data.get('is_read', False),
                data.get('subject'),
                data.get('created_at')
            )
        except Exception as e:
            print(f"Error getting message: {e}")
            return None

