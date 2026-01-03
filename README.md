# Secure Email System - COMP 417 Project

A secure email system that ensures user authentication, message confidentiality, integrity verification, and sender authentication using cryptographic techniques.

## Features

- **User Registration & Authentication**: Secure password hashing using bcrypt
- **Message Confidentiality**: AES-256-CBC symmetric encryption with RSA-encrypted keys
- **Message Integrity**: SHA-256 hashing for integrity verification
- **Digital Signatures**: RSA-based digital signatures for sender authentication
- **Database Storage**: SQLite database for users, keys, and encrypted messages

## Requirements

- Python 3.7+
- Required packages (install via `pip install -r requirements.txt`):
  - bcrypt==4.1.2
  - cryptography==42.0.5

## Installation

1. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Activate virtual environment (if not already activated):
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Run the application:
```bash
python main.py
```

3. Or run the test script to verify everything works:
```bash
python test_system.py
```

### Application Flow

1. **Register**: Create a new account with username and password
2. **Login**: Authenticate with your credentials
3. **Send Email**: 
   - Enter recipient username
   - Type your message
   - Message is automatically encrypted and signed
4. **View Inbox**: See list of received messages
5. **Read Email**: 
   - Enter message ID
   - Message is decrypted and verified automatically
   - Integrity and signature verification results are displayed

## Cryptographic Implementation

### Password Storage
- **Algorithm**: bcrypt with automatic salt generation
- Passwords are hashed before storage in database

### Message Encryption
- **Symmetric Encryption**: AES-256-CBC
- **Key Encryption**: RSA-OAEP with SHA-256
- Symmetric key is encrypted with recipient's public key

### Integrity & Authentication
- **Hashing**: SHA-256 for message integrity
- **Digital Signatures**: RSA-PSS with SHA-256
- Hash is signed with sender's private key

### Key Management
- **Key Size**: RSA 2048-bit keys
- Each user gets a unique RSA key pair on registration
- Public keys stored for encryption/verification
- Private keys stored for decryption/signing

## Database Schema

- **users**: Stores username and hashed password
- **public_keys**: Stores user's RSA public key
- **private_keys**: Stores user's RSA private key
- **messages**: Stores encrypted messages, encrypted keys, hashes, and signatures

## Error Handling

The system includes error handling for:
- Failed login attempts
- Invalid usernames
- Message verification failures
- Decryption errors
- Integrity check failures
- Signature verification failures

## Security Notes

- All cryptographic operations use built-in, secure algorithms
- Private keys are stored in database (in production, consider additional encryption)
- Passwords are never stored in plaintext
- Messages are encrypted end-to-end
- Digital signatures prevent message tampering and verify sender identity

