# Secure Email System - COMP 417 Project

A secure email system that ensures user authentication, message confidentiality, integrity verification, and sender authentication using cryptographic techniques.

## Features

- **User Registration & Authentication**: Secure password hashing using bcrypt
- **Message Confidentiality**: AES-256-CBC symmetric encryption with RSA-encrypted keys
- **Message Integrity**: SHA-256 hashing for integrity verification
- **Digital Signatures**: RSA-based digital signatures for sender authentication
- **Database Storage**: SQLite database for users, keys, and encrypted messages

## Requirements

- **Python 3.8 or higher** (Python 3.9+ recommended)
- pip (Python package installer)
- Windows 10/11, Linux, or macOS

## Installation

### Windows Installation

1. **Check Python Installation:**
   ```cmd
   python --version
   ```
   If Python is not installed, download from [python.org](https://www.python.org/downloads/)
   - **Important**: During installation, check "Add Python to PATH"

2. **Open Command Prompt or PowerShell:**
   - Navigate to the project directory:
   ```cmd
   cd path\to\crypto_project
   ```

3. **Create a virtual environment:**
   ```cmd
   python -m venv venv
   ```
   If `python` doesn't work, try `py`:
   ```cmd
   py -m venv venv
   ```

4. **Activate the virtual environment:**
   ```cmd
   venv\Scripts\activate
   ```
   You should see `(venv)` at the beginning of your command prompt.

5. **Upgrade pip (recommended):**
   ```cmd
   python -m pip install --upgrade pip
   ```

6. **Install dependencies:**
   ```cmd
   pip install -r requirements.txt
   ```

### Linux/macOS Installation

1. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   ```

2. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate
   ```

3. **Upgrade pip (recommended):**
   ```bash
   python3 -m pip install --upgrade pip
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Windows

1. **Activate virtual environment (if not already activated):**
   ```cmd
   venv\Scripts\activate
   ```

2. **Run the application:**
   ```cmd
   python main.py
   ```
   
   Or use the batch script (double-click `run.bat` or run in command prompt):
   ```cmd
   run.bat
   ```

3. **Run the test script to verify everything works:**
   ```cmd
   python test_system.py
   ```

### Linux/macOS

1. **Activate virtual environment (if not already activated):**
   ```bash
   source venv/bin/activate
   ```

2. **Run the application:**
   ```bash
   python main.py
   ```
   
   Or use the shell script:
   ```bash
   ./run.sh
   ```

3. **Run the test script:**
   ```bash
   python test_system.py
   ```

### Application Flow

1. **Register**: Create a new account with username and password
2. **Login**: Authenticate with your credentials
3. **Send Email**: 
   - Enter recipient username
   - Type your message (press Enter twice to finish)
   - Message is automatically encrypted and signed
4. **View Inbox**: See list of received messages
5. **Read Email**: 
   - Enter message ID
   - Message is decrypted and verified automatically
   - Integrity and signature verification results are displayed

## Troubleshooting

### Windows Issues

**"python is not recognized"**
- Make sure Python is added to PATH during installation
- Try using `py` instead of `python`
- Reinstall Python and check "Add Python to PATH" option

**"venv\Scripts\activate is not recognized"**
- Make sure you're in the project directory
- Check that the `venv` folder exists
- Try: `python -m venv venv` again

**"pip install fails" or "cryptography installation fails"**
- Upgrade pip first: `python -m pip install --upgrade pip`
- Install build tools:
  ```cmd
  pip install --upgrade pip setuptools wheel
  pip install -r requirements.txt
  ```
- If cryptography still fails, you may need Visual C++ Build Tools:
  - Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
  - Or install pre-built wheels:
    ```cmd
    pip install --only-binary :all: cryptography
    pip install -r requirements.txt
    ```

**"ModuleNotFoundError"**
- Make sure virtual environment is activated (you should see `(venv)` in prompt)
- Reinstall dependencies: `pip install -r requirements.txt`

**Database errors**
- Delete `secure_email.db` file and restart the application
- The database will be recreated automatically

### General Issues

- **Import errors**: Make sure the virtual environment is activated
- **Permission errors**: Run command prompt as administrator (Windows) or use `sudo` (Linux/macOS)
- **Port conflicts**: Close other applications using the same resources

## Dependencies

The project uses the following packages (see `requirements.txt`):

- **bcrypt** (>=4.0.0): Secure password hashing
- **cryptography** (>=41.0.0): Cryptographic primitives (RSA, AES, hashing, signatures)

These versions are compatible with Python 3.8+ on Windows, Linux, and macOS.

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

## Project Structure

```
crypto_project/
├── database.py          # Database management
├── crypto_utils.py      # Cryptographic operations
├── email_system.py      # Email system logic
├── main.py              # Main application interface
├── test_system.py       # Automated test script
├── requirements.txt     # Python dependencies
├── README.md            # This file
├── run.bat              # Windows run script
├── run.sh               # Linux/macOS run script
└── secure_email.db      # SQLite database (created automatically)
```

## License

This project is created for COMP 417 Introduction to Cryptography course.
