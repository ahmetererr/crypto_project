"""
Database module for storing users, public keys, and messages
Supports both SQLite (local) and Firebase Firestore (cloud)
"""
import sqlite3
import os
from typing import Optional, List, Tuple
from config import DB_TYPE, SQLITE_DB_NAME, FIREBASE_CONFIG

DB_NAME = "secure_email.db"


class Database:
    def __init__(self, db_name: str = DB_NAME):
        """
        Initialize database based on DB_TYPE in config
        Supports SQLite (local) and Firebase Firestore (cloud)
        """
        self.db_type = DB_TYPE
        self.db_name = db_name
        
        if self.db_type == 'firebase':
            # Use Firebase Firestore
            from database_firebase import DatabaseFirebase
            credentials_path = FIREBASE_CONFIG.get('credentials_path')
            project_id = FIREBASE_CONFIG.get('project_id')
            
            if not credentials_path:
                raise Exception("FIREBASE_CREDENTIALS_PATH must be set in environment or config")
            
            self.firebase_db = DatabaseFirebase(credentials_path, project_id)
        else:
            # Use SQLite (default)
            self.init_database()
    
    def get_connection(self):
        """Get database connection (SQLite only)"""
        if self.db_type == 'firebase':
            return self.firebase_db  # Return Firebase instance
        return sqlite3.connect(self.db_name)
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table: stores username and hashed password
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Public keys table: stores user's public key
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS public_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                public_key TEXT NOT NULL,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')
        
        # Private keys table: stores user's encrypted private key
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS private_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                private_key TEXT NOT NULL,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')
        
        # Messages table: stores encrypted messages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                encrypted_content TEXT NOT NULL,
                encrypted_symmetric_key TEXT NOT NULL,
                message_hash TEXT NOT NULL,
                digital_signature TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                subject TEXT,
                cc TEXT,
                bcc TEXT,
                reply_to INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender) REFERENCES users(username),
                FOREIGN KEY (recipient) REFERENCES users(username),
                FOREIGN KEY (reply_to) REFERENCES messages(id)
            )
        ''')
        
        # Add new columns if they don't exist
        try:
            cursor.execute('ALTER TABLE messages ADD COLUMN cc TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists
        try:
            cursor.execute('ALTER TABLE messages ADD COLUMN bcc TEXT')
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute('ALTER TABLE messages ADD COLUMN reply_to INTEGER')
        except sqlite3.OperationalError:
            pass
        
        # Add is_read column if it doesn't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE messages ADD COLUMN is_read INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Add subject column if it doesn't exist
        try:
            cursor.execute('ALTER TABLE messages ADD COLUMN subject TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        conn.commit()
        conn.close()
    
    def add_user(self, username: str, password_hash: str) -> bool:
        """Add a new user to the database"""
        if self.db_type == 'firebase':
            return self.firebase_db.add_user(username, password_hash)
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                (username, password_hash)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False  # Username already exists
    
    def get_user_password_hash(self, username: str) -> Optional[str]:
        """Get password hash for a user"""
        if self.db_type == 'firebase':
            return self.firebase_db.get_user_password_hash(username)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT password_hash FROM users WHERE username = ?',
            (username,)
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def user_exists(self, username: str) -> bool:
        """Check if user exists"""
        if self.db_type == 'firebase':
            return self.firebase_db.user_exists(username)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def save_public_key(self, username: str, public_key: str) -> bool:
        """Save user's public key"""
        if self.db_type == 'firebase':
            return self.firebase_db.save_public_key(username, public_key)
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR REPLACE INTO public_keys (username, public_key) VALUES (?, ?)',
                (username, public_key)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving public key: {e}")
            return False
    
    def save_private_key(self, username: str, private_key: str) -> bool:
        """Save user's private key"""
        if self.db_type == 'firebase':
            return self.firebase_db.save_private_key(username, private_key)
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR REPLACE INTO private_keys (username, private_key) VALUES (?, ?)',
                (username, private_key)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving private key: {e}")
            return False
    
    def get_public_key(self, username: str) -> Optional[str]:
        """Get user's public key"""
        if self.db_type == 'firebase':
            return self.firebase_db.get_public_key(username)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT public_key FROM public_keys WHERE username = ?',
            (username,)
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def get_private_key(self, username: str) -> Optional[str]:
        """Get user's private key"""
        if self.db_type == 'firebase':
            return self.firebase_db.get_private_key(username)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT private_key FROM private_keys WHERE username = ?',
            (username,)
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def save_message(self, sender: str, recipient: str, encrypted_content: str,
                     encrypted_symmetric_key: str, message_hash: str, digital_signature: str, 
                     subject: str = None, cc: str = None, bcc: str = None, reply_to: int = None,
                     sender_copy_encrypted_content: str = None, sender_copy_encrypted_key: str = None) -> bool:
        """Save encrypted message"""
        if self.db_type == 'firebase':
            return self.firebase_db.save_message(sender, recipient, encrypted_content,
                                                encrypted_symmetric_key, message_hash, digital_signature, 
                                                subject, cc, bcc, reply_to, sender_copy_encrypted_content, sender_copy_encrypted_key)
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO messages (sender, recipient, encrypted_content, 
                    encrypted_symmetric_key, message_hash, digital_signature, subject, cc, bcc, reply_to)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (sender, recipient, encrypted_content, encrypted_symmetric_key,
                 message_hash, digital_signature, subject, cc, bcc, reply_to)
            )
            message_id = cursor.lastrowid
            
            # Save sender's copy if provided (encrypted with sender's own key)
            if sender_copy_encrypted_content and sender_copy_encrypted_key:
                cursor.execute(
                    '''INSERT INTO messages (sender, recipient, encrypted_content, 
                        encrypted_symmetric_key, message_hash, digital_signature, subject, cc, bcc, reply_to)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (sender, sender, sender_copy_encrypted_content, sender_copy_encrypted_key,
                     message_hash, digital_signature, subject, cc, bcc, reply_to)
                )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving message: {e}")
            return False
    
    def get_messages_for_user(self, username: str) -> List[Tuple]:
        """Get all messages for a user (inbox)"""
        if self.db_type == 'firebase':
            return self.firebase_db.get_messages_for_user(username)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT id, sender, recipient, encrypted_content, encrypted_symmetric_key,
               message_hash, digital_signature, is_read, subject, cc, bcc, reply_to, created_at
               FROM messages WHERE recipient = ? ORDER BY created_at DESC''',
            (username,)
        )
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_sent_messages_for_user(self, username: str) -> List[Tuple]:
        """Get all messages sent by a user"""
        if self.db_type == 'firebase':
            return self.firebase_db.get_sent_messages_for_user(username)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT id, sender, recipient, encrypted_content, encrypted_symmetric_key,
               message_hash, digital_signature, is_read, subject, cc, bcc, reply_to, created_at
               FROM messages WHERE sender = ? AND recipient != sender ORDER BY created_at DESC''',
            (username,)
        )
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_all_usernames(self) -> List[str]:
        """Get all usernames for autocomplete"""
        if self.db_type == 'firebase':
            return self.firebase_db.get_all_usernames()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM users ORDER BY username')
        results = cursor.fetchall()
        conn.close()
        return [row[0] for row in results]
    
    def mark_as_read(self, message_id) -> bool:
        """Mark message as read (int for SQLite, str for Firebase)"""
        if self.db_type == 'firebase':
            return self.firebase_db.mark_as_read(str(message_id))
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE messages SET is_read = 1 WHERE id = ?',
                (int(message_id),)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error marking message as read: {e}")
            return False
    
    def get_message_by_id(self, message_id) -> Optional[Tuple]:
        """Get message by ID (int for SQLite, str for Firebase)"""
        if self.db_type == 'firebase':
            return self.firebase_db.get_message_by_id(str(message_id))
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT id, sender, recipient, encrypted_content, encrypted_symmetric_key,
                   message_hash, digital_signature, is_read, subject, cc, bcc, reply_to, created_at
                   FROM messages WHERE id = ?''',
                (int(message_id),)
            )
            result = cursor.fetchone()
            conn.close()
            return result
        except Exception as e:
            print(f"Error getting message: {e}")
            return None

