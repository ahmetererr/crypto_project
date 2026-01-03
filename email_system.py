"""
Main email system logic for sending and receiving secure emails
"""
from database import Database
from crypto_utils import CryptoUtils
from typing import Optional, Tuple, Dict, List


class EmailSystem:
    def __init__(self):
        self.db = Database()
        self.crypto = CryptoUtils()
    
    def register_user(self, username: str, password: str) -> Tuple[bool, str]:
        """Register a new user and generate key pair"""
        if self.db.user_exists(username):
            return False, "Username already exists"
        
        # Hash password
        password_hash = self.crypto.hash_password(password)
        
        # Add user to database
        if not self.db.add_user(username, password_hash):
            return False, "Failed to register user"
        
        # Generate RSA key pair
        private_key, public_key = self.crypto.generate_rsa_key_pair()
        
        # Serialize and save keys
        private_key_str = self.crypto.serialize_private_key(private_key)
        public_key_str = self.crypto.serialize_public_key(public_key)
        
        self.db.save_private_key(username, private_key_str)
        self.db.save_public_key(username, public_key_str)
        
        return True, "User registered successfully"
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, str]:
        """Authenticate user by verifying password"""
        password_hash = self.db.get_user_password_hash(username)
        
        if password_hash is None:
            return False, "User does not exist"
        
        if not self.crypto.verify_password(password, password_hash):
            return False, "Invalid password"
        
        return True, "Authentication successful"
    
    def send_email(self, sender: str, recipient: str, message: str) -> Tuple[bool, str]:
        """Send encrypted and signed email"""
        # Check if sender exists
        if not self.db.user_exists(sender):
            return False, "Sender does not exist"
        
        # Check if recipient exists
        if not self.db.user_exists(recipient):
            return False, "Recipient does not exist"
        
        # Get recipient's public key
        recipient_public_key_str = self.db.get_public_key(recipient)
        if recipient_public_key_str is None:
            return False, "Recipient's public key not found"
        
        recipient_public_key = self.crypto.deserialize_public_key(recipient_public_key_str)
        
        # Get sender's private key
        sender_private_key_str = self.db.get_private_key(sender)
        if sender_private_key_str is None:
            return False, "Sender's private key not found"
        
        sender_private_key = self.crypto.deserialize_private_key(sender_private_key_str)
        
        # Step 1: Generate symmetric key and encrypt message
        symmetric_key = self.crypto.generate_symmetric_key()
        encrypted_content, iv = self.crypto.encrypt_symmetric(message, symmetric_key)
        
        # Step 2: Encrypt symmetric key with recipient's public key
        encrypted_symmetric_key = self.crypto.encrypt_with_public_key(symmetric_key, recipient_public_key)
        
        # Step 3: Generate hash of the message
        message_hash = self.crypto.hash_message(message)
        
        # Step 4: Sign the hash with sender's private key
        digital_signature = self.crypto.sign_message(message_hash, sender_private_key)
        
        # Store IV with encrypted content (combine them)
        encrypted_content_with_iv = f"{iv}:{encrypted_content}"
        
        # Save message to database
        if self.db.save_message(sender, recipient, encrypted_content_with_iv,
                               encrypted_symmetric_key, message_hash, digital_signature):
            return True, "Email sent successfully"
        else:
            return False, "Failed to save message"
    
    def receive_email(self, username: str, message_id: int) -> Tuple[bool, Optional[Dict], str]:
        """Receive and decrypt email, verify integrity and signature"""
        # Get all messages for user
        messages = self.db.get_messages_for_user(username)
        
        # Find the specific message
        message_data = None
        for msg in messages:
            if msg[0] == message_id:  # msg[0] is the id
                message_data = msg
                break
        
        if message_data is None:
            return False, None, "Message not found"
        
        msg_id, sender, recipient, encrypted_content_with_iv, encrypted_symmetric_key, \
            message_hash, digital_signature, created_at = message_data
        
        # Get recipient's private key
        recipient_private_key_str = self.db.get_private_key(username)
        if recipient_private_key_str is None:
            return False, None, "Private key not found"
        
        recipient_private_key = self.crypto.deserialize_private_key(recipient_private_key_str)
        
        # Get sender's public key
        sender_public_key_str = self.db.get_public_key(sender)
        if sender_public_key_str is None:
            return False, None, "Sender's public key not found"
        
        sender_public_key = self.crypto.deserialize_public_key(sender_public_key_str)
        
        try:
            # Step 1: Decrypt symmetric key using recipient's private key
            symmetric_key = self.crypto.decrypt_with_private_key(encrypted_symmetric_key, recipient_private_key)
            
            # Step 2: Decrypt message content
            iv_str, encrypted_content = encrypted_content_with_iv.split(':', 1)
            decrypted_message = self.crypto.decrypt_symmetric(encrypted_content, iv_str, symmetric_key)
            
            # Step 3: Verify message integrity (hash)
            computed_hash = self.crypto.hash_message(decrypted_message)
            if computed_hash != message_hash:
                return False, None, "Message integrity verification failed - message may have been tampered with"
            
            # Step 4: Verify digital signature
            if not self.crypto.verify_signature(message_hash, digital_signature, sender_public_key):
                return False, None, "Digital signature verification failed - message may not be from claimed sender"
            
            # All verifications passed
            result = {
                'id': msg_id,
                'sender': sender,
                'recipient': recipient,
                'message': decrypted_message,
                'created_at': created_at,
                'integrity_verified': True,
                'signature_verified': True
            }
            
            return True, result, "Email received and verified successfully"
            
        except Exception as e:
            return False, None, f"Error decrypting message: {str(e)}"
    
    def list_messages(self, username: str) -> List[Dict]:
        """List all messages for a user (without decrypting)"""
        messages = self.db.get_messages_for_user(username)
        result = []
        for msg in messages:
            result.append({
                'id': msg[0],
                'sender': msg[1],
                'recipient': msg[2],
                'created_at': msg[7]
            })
        return result

