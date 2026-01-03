"""
Main application interface for the secure email system
"""
from email_system import EmailSystem
import sys


class EmailClient:
    def __init__(self):
        self.email_system = EmailSystem()
        self.current_user = None
    
    def print_menu(self):
        """Print main menu"""
        print("\n" + "="*50)
        print("Secure Email System")
        print("="*50)
        if self.current_user:
            print(f"Logged in as: {self.current_user}")
            print("1. Send Email")
            print("2. View Inbox")
            print("3. Read Email")
            print("4. Logout")
            print("5. Exit")
        else:
            print("1. Register")
            print("2. Login")
            print("3. Exit")
        print("="*50)
    
    def register(self):
        """Handle user registration"""
        print("\n--- User Registration ---")
        username = input("Enter username: ").strip()
        if not username:
            print("Error: Username cannot be empty")
            return
        
        password = input("Enter password: ").strip()
        if not password:
            print("Error: Password cannot be empty")
            return
        
        success, message = self.email_system.register_user(username, password)
        if success:
            print(f"✓ {message}")
            print("✓ RSA key pair generated and stored")
        else:
            print(f"✗ Error: {message}")
    
    def login(self):
        """Handle user login"""
        print("\n--- User Login ---")
        username = input("Enter username: ").strip()
        password = input("Enter password: ").strip()
        
        success, message = self.email_system.authenticate_user(username, password)
        if success:
            self.current_user = username
            print(f"✓ {message}")
        else:
            print(f"✗ Error: {message}")
    
    def send_email(self):
        """Handle sending email"""
        if not self.current_user:
            print("Error: You must be logged in")
            return
        
        print("\n--- Send Email ---")
        recipient = input("Enter recipient username: ").strip()
        if not recipient:
            print("Error: Recipient cannot be empty")
            return
        
        print("Enter message (press Enter on empty line to finish):")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        
        message = "\n".join(lines)
        if not message:
            print("Error: Message cannot be empty")
            return
        
        success, msg = self.email_system.send_email(self.current_user, recipient, message)
        if success:
            print(f"✓ {msg}")
            print("✓ Message encrypted and signed")
        else:
            print(f"✗ Error: {msg}")
    
    def view_inbox(self):
        """Display inbox"""
        if not self.current_user:
            print("Error: You must be logged in")
            return
        
        print("\n--- Inbox ---")
        messages = self.email_system.list_messages(self.current_user)
        
        if not messages:
            print("No messages in inbox")
            return
        
        print(f"\nYou have {len(messages)} message(s):\n")
        for msg in messages:
            print(f"ID: {msg['id']} | From: {msg['sender']} | Date: {msg['created_at']}")
    
    def read_email(self):
        """Handle reading and verifying email"""
        if not self.current_user:
            print("Error: You must be logged in")
            return
        
        print("\n--- Read Email ---")
        try:
            message_id = int(input("Enter message ID: ").strip())
        except ValueError:
            print("Error: Invalid message ID")
            return
        
        success, email_data, message = self.email_system.receive_email(self.current_user, message_id)
        
        if success and email_data:
            print(f"\n✓ {message}")
            print("\n" + "-"*50)
            print(f"From: {email_data['sender']}")
            print(f"To: {email_data['recipient']}")
            print(f"Date: {email_data['created_at']}")
            print(f"Integrity Verified: {'✓ Yes' if email_data['integrity_verified'] else '✗ No'}")
            print(f"Signature Verified: {'✓ Yes' if email_data['signature_verified'] else '✗ No'}")
            print("-"*50)
            print("Message:")
            print(email_data['message'])
            print("-"*50)
        else:
            print(f"✗ Error: {message}")
    
    def logout(self):
        """Handle logout"""
        self.current_user = None
        print("✓ Logged out successfully")
    
    def run(self):
        """Main application loop"""
        print("Welcome to the Secure Email System!")
        
        while True:
            self.print_menu()
            choice = input("\nEnter your choice: ").strip()
            
            if not self.current_user:
                # Not logged in
                if choice == "1":
                    self.register()
                elif choice == "2":
                    self.login()
                elif choice == "3":
                    print("Goodbye!")
                    sys.exit(0)
                else:
                    print("Invalid choice. Please try again.")
            else:
                # Logged in
                if choice == "1":
                    self.send_email()
                elif choice == "2":
                    self.view_inbox()
                elif choice == "3":
                    self.read_email()
                elif choice == "4":
                    self.logout()
                elif choice == "5":
                    print("Goodbye!")
                    sys.exit(0)
                else:
                    print("Invalid choice. Please try again.")


if __name__ == "__main__":
    try:
        client = EmailClient()
        client.run()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)

