"""
Test script to verify the secure email system works correctly
"""
from email_system import EmailSystem

def test_system():
    print("="*60)
    print("Testing Secure Email System")
    print("="*60)
    
    email_system = EmailSystem()
    
    # Test 1: Register users
    print("\n[Test 1] Registering users...")
    success, msg = email_system.register_user("alice", "password123")
    print(f"Register alice: {msg}")
    assert success, "Failed to register alice"
    
    success, msg = email_system.register_user("bob", "password456")
    print(f"Register bob: {msg}")
    assert success, "Failed to register bob"
    
    # Test 2: Authentication
    print("\n[Test 2] Testing authentication...")
    success, msg = email_system.authenticate_user("alice", "password123")
    print(f"Login alice: {msg}")
    assert success, "Failed to authenticate alice"
    
    success, msg = email_system.authenticate_user("alice", "wrongpassword")
    print(f"Login alice with wrong password: {msg}")
    assert not success, "Should have failed with wrong password"
    
    # Test 3: Send email
    print("\n[Test 3] Sending email...")
    test_message = "Hello Bob! This is a test message from Alice."
    success, msg = email_system.send_email("alice", "bob", test_message)
    print(f"Send email: {msg}")
    assert success, "Failed to send email"
    
    # Test 4: List messages
    print("\n[Test 4] Listing messages...")
    messages = email_system.list_messages("bob")
    print(f"Bob has {len(messages)} message(s)")
    assert len(messages) > 0, "Bob should have received a message"
    
    # Test 5: Receive and verify email
    print("\n[Test 5] Receiving and verifying email...")
    message_id = messages[0]['id']
    success, email_data, msg = email_system.receive_email("bob", message_id)
    print(f"Receive email: {msg}")
    assert success, "Failed to receive email"
    assert email_data is not None, "Email data should not be None"
    assert email_data['message'] == test_message, "Decrypted message should match original"
    assert email_data['integrity_verified'], "Integrity should be verified"
    assert email_data['signature_verified'], "Signature should be verified"
    
    print("\n" + "="*60)
    print("✓ All tests passed!")
    print("="*60)

if __name__ == "__main__":
    try:
        test_system()
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

