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
    
    def send_email(self, sender: str, recipient: str, message: str, subject: str = None, 
                   cc: str = None, bcc: str = None, reply_to: int = None) -> Tuple[bool, str]:
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
        
        # Get sender's keys
        sender_private_key_str = self.db.get_private_key(sender)
        if sender_private_key_str is None:
            return False, "Sender's private key not found"
        
        sender_private_key = self.crypto.deserialize_private_key(sender_private_key_str)
        
        # Get sender's public key for sender copy
        sender_public_key_str = self.db.get_public_key(sender)
        if sender_public_key_str is None:
            return False, "Sender's public key not found"
        
        sender_public_key = self.crypto.deserialize_public_key(sender_public_key_str)
        
        # Step 1: Generate symmetric key and encrypt message
        symmetric_key = self.crypto.generate_symmetric_key()
        encrypted_content, iv = self.crypto.encrypt_symmetric(message, symmetric_key)
        
        # Step 2: Encrypt symmetric key with recipient's public key
        encrypted_symmetric_key = self.crypto.encrypt_with_public_key(symmetric_key, recipient_public_key)
        
        # Step 3: Create sender's copy (encrypted with sender's own public key)
        sender_symmetric_key = self.crypto.generate_symmetric_key()
        sender_encrypted_content, sender_iv = self.crypto.encrypt_symmetric(message, sender_symmetric_key)
        sender_encrypted_key = self.crypto.encrypt_with_public_key(sender_symmetric_key, sender_public_key)
        sender_encrypted_content_with_iv = f"{sender_iv}:{sender_encrypted_content}"
        
        # Step 4: Generate hash of the message
        message_hash = self.crypto.hash_message(message)
        
        # Step 5: Sign the hash with sender's private key
        digital_signature = self.crypto.sign_message(message_hash, sender_private_key)
        
        # Store IV with encrypted content (combine them)
        encrypted_content_with_iv = f"{iv}:{encrypted_content}"
        
        # Save message to database (both recipient copy and sender copy)
        if self.db.save_message(sender, recipient, encrypted_content_with_iv,
                               encrypted_symmetric_key, message_hash, digital_signature, 
                               subject, cc, bcc, reply_to,
                               sender_encrypted_content_with_iv, sender_encrypted_key):
            return True, "Email sent successfully"
        else:
            return False, "Failed to save message"
    
    def receive_email(self, username: str, message_id: int) -> Tuple[bool, Optional[Dict], str]:
        """Receive and decrypt email, verify integrity and signature"""
        # Try to get message by ID directly (works for both inbox and sent)
        message_data = self.db.get_message_by_id(message_id)
        
        if message_data is None:
            return False, None, "Message not found"
        
        # Handle different message formats
        if len(message_data) == 8:
            msg_id, sender, recipient, encrypted_content_with_iv, encrypted_symmetric_key, \
                message_hash, digital_signature, created_at = message_data
            is_read = 0
            subject = None
            cc = None
            bcc = None
            reply_to = None
        elif len(message_data) == 10:
            msg_id, sender, recipient, encrypted_content_with_iv, encrypted_symmetric_key, \
                message_hash, digital_signature, is_read, subject, created_at = message_data
            cc = None
            bcc = None
            reply_to = None
        else:
            # New format with cc, bcc, reply_to
            msg_id, sender, recipient, encrypted_content_with_iv, encrypted_symmetric_key, \
                message_hash, digital_signature, is_read, subject, cc, bcc, reply_to, created_at = message_data
        
        # Check if user is either recipient or sender
        if username != recipient and username != sender:
            return False, None, "You don't have permission to view this message"
        
        # Determine if user is sender or recipient
        is_sender = (username == sender)
        is_sender_copy = (is_sender and recipient == sender)  # Sender's own copy
        
        # For sent messages (sender's copy), decrypt with sender's own key
        if is_sender_copy:
            # Get sender's private key
            sender_private_key_str = self.db.get_private_key(username)
            if sender_private_key_str is None:
                return False, None, "Private key not found"
            
            sender_private_key = self.crypto.deserialize_private_key(sender_private_key_str)
            
            # Get sender's public key for signature verification
            sender_public_key_str = self.db.get_public_key(sender)
            if sender_public_key_str is None:
                return False, None, "Sender's public key not found"
            
            sender_public_key = self.crypto.deserialize_public_key(sender_public_key_str)
            
            try:
                # Decrypt using sender's own key
                symmetric_key = self.crypto.decrypt_with_private_key(encrypted_symmetric_key, sender_private_key)
                iv_str, encrypted_content = encrypted_content_with_iv.split(':', 1)
                decrypted_message = self.crypto.decrypt_symmetric(encrypted_content, iv_str, symmetric_key)
                
                # Verify integrity
                computed_hash = self.crypto.hash_message(decrypted_message)
                if computed_hash != message_hash:
                    return False, None, "Message integrity verification failed"
                
                # Verify digital signature
                signature_verified = self.crypto.verify_signature(message_hash, digital_signature, sender_public_key)
                if not signature_verified:
                    return False, None, "Digital signature verification failed - message may have been tampered with"
                
                result = {
                    'id': msg_id,
                    'sender': sender,
                    'recipient': recipient,
                    'message': decrypted_message,
                    'subject': subject or '(No Subject)',
                    'cc': cc,
                    'bcc': bcc,
                    'reply_to': reply_to,
                    'created_at': created_at,
                    'is_read': bool(is_read),
                    'integrity_verified': True,
                    'signature_verified': True,  # Verified above, so always True here
                    'is_sent': True
                }
                return True, result, "Sent message (decrypted from your copy)"
            except Exception as e:
                return False, None, f"Error decrypting sent message: {str(e)}"
        
        # For received messages, decrypt normally
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
            
            # Mark as read (only for received messages)
            self.db.mark_as_read(msg_id)
            
            # All verifications passed
            result = {
                'id': msg_id,
                'sender': sender,
                'recipient': recipient,
                'message': decrypted_message,
                'subject': subject or '(No Subject)',
                'cc': cc,
                'bcc': bcc,
                'reply_to': reply_to,
                'created_at': created_at,
                'is_read': True,
                'integrity_verified': True,
                'signature_verified': True,
                'is_sent': False
            }
            
            return True, result, "Email received and verified successfully"
            
        except Exception as e:
            return False, None, f"Error decrypting message: {str(e)}"
    
    def list_messages(self, username: str) -> List[Dict]:
        """List all messages for a user (inbox, without decrypting)"""
        messages = self.db.get_messages_for_user(username)
        result = []
        for msg in messages:
            # Handle different formats
            if len(msg) == 8:
                msg_id, sender, recipient, _, _, _, _, created_at = msg
                is_read = 0
                subject = None
                reply_to = None
            elif len(msg) == 10:
                msg_id, sender, recipient, _, _, _, _, is_read, subject, created_at = msg
                reply_to = None
            else:
                msg_id, sender, recipient, _, _, _, _, is_read, subject, cc, bcc, reply_to, created_at = msg
            
            result.append({
                'id': msg_id,
                'sender': sender,
                'recipient': recipient,
                'subject': subject or '(No Subject)',
                'is_read': bool(is_read),
                'reply_to': reply_to,
                'created_at': created_at
            })
        return result
    
    def list_sent_messages(self, username: str) -> List[Dict]:
        """List all messages sent by a user (without decrypting)"""
        # Get both sent messages and sender's copies
        sent_messages = self.db.get_sent_messages_for_user(username)
        # Also get sender's own copies (where recipient == sender)
        all_inbox = self.db.get_messages_for_user(username)
        sender_copies = [msg for msg in all_inbox if len(msg) > 1 and msg[1] == username and msg[2] == username]
        
        # Create a map of sender copies by subject+time to find original recipient
        sender_copy_map = {}
        for msg in sender_copies:
            if len(msg) >= 10:
                subject = msg[9] if len(msg) > 9 else None
                created_at = msg[-1] if len(msg) > 0 else None
                key = f"{subject or ''}_{created_at}"
                sender_copy_map[key] = msg
        
        # Combine and deduplicate by subject and time
        all_messages = {}
        for msg in sent_messages:
            # Handle different formats
            if len(msg) == 8:
                msg_id, sender, recipient, _, _, _, _, created_at = msg
                is_read = 0
                subject = None
                reply_to = None
            elif len(msg) == 10:
                msg_id, sender, recipient, _, _, _, _, is_read, subject, created_at = msg
                reply_to = None
            else:
                msg_id, sender, recipient, _, _, _, _, is_read, subject, cc, bcc, reply_to, created_at = msg
            
            # Use subject+time as key to avoid duplicates
            key = f"{subject or ''}_{created_at}"
            all_messages[key] = {
                'id': msg_id,
                'sender': sender,
                'recipient': recipient,
                'subject': subject or '(No Subject)',
                'is_read': bool(is_read),
                'reply_to': reply_to,
                'created_at': created_at
            }
        
        result = list(all_messages.values())
        result.sort(key=lambda x: x['created_at'], reverse=True)
        return result
    
    def get_all_usernames(self) -> List[str]:
        """Get all usernames for autocomplete"""
        return self.db.get_all_usernames()
    
    def reply_email(self, original_message_id, replier: str, reply_message: str, subject: str = None) -> Tuple[bool, str]:
        """Reply to an email"""
        # Get original message
        original_msg = self.db.get_message_by_id(original_message_id)
        if not original_msg:
            return False, "Original message not found"
        
        # Extract sender from original message
        original_sender = original_msg[1]  # sender is at index 1
        
        # Get original subject
        if len(original_msg) >= 10:
            original_subject = original_msg[9] if len(original_msg) > 9 else None
        else:
            original_subject = None
        
        # Create reply subject if not provided
        if not subject:
            if original_subject and original_subject.startswith('Re: '):
                subject = original_subject
            else:
                subject = f"Re: {original_subject or 'No Subject'}"
        
        # Include original message in reply
        # Get original message content if available
        try:
            success, original_email_data, _ = self.receive_email(replier, original_message_id)
            if success and original_email_data:
                original_content = original_email_data.get('message', '')
                reply_with_thread = f"{reply_message}\n\n--- Original Message ---\nFrom: {original_sender}\nSubject: {original_subject or 'No Subject'}\n\n{original_content}"
            else:
                reply_with_thread = reply_message
        except:
            reply_with_thread = reply_message
        
        # Send the reply with reply_to reference
        return self.send_email(replier, original_sender, reply_with_thread, subject, reply_to=original_message_id)
    
    def forward_email(self, original_message_id, forwarder: str, recipient: str, forward_message: str = None, subject: str = None) -> Tuple[bool, str]:
        """Forward an email"""
        # Get original message
        original_msg = self.db.get_message_by_id(original_message_id)
        if not original_msg:
            return False, "Original message not found"
        
        # Decrypt original message
        username = forwarder
        success, email_data, _ = self.receive_email(username, original_message_id)
        if not success:
            return False, "Could not decrypt original message"
        
        # Create forwarded message content
        original_sender = email_data['sender']
        original_subject = email_data.get('subject', '(No Subject)')
        original_content = email_data['message']
        
        # Create forward message
        if forward_message:
            forwarded_content = f"{forward_message}\n\n--- Forwarded Message ---\nFrom: {original_sender}\nSubject: {original_subject}\n\n{original_content}"
        else:
            forwarded_content = f"--- Forwarded Message ---\nFrom: {original_sender}\nSubject: {original_subject}\n\n{original_content}"
        
        # Create forward subject
        if not subject:
            if original_subject.startswith('Fwd: ') or original_subject.startswith('Fw: '):
                subject = original_subject
            else:
                subject = f"Fwd: {original_subject}"
        
        # Send the forwarded email
        return self.send_email(forwarder, recipient, forwarded_content, subject)

