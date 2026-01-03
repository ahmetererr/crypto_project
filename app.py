"""
Flask web server for Secure Email System
Allows remote access to the email system via REST API and web interface
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from email_system import EmailSystem
import os
import base64

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for sessions

# Initialize email system
email_system = EmailSystem()


@app.route('/')
def index():
    """Home page - redirect to login if not authenticated"""
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            return render_template('login.html', error='Username and password are required')
        
        success, message = email_system.authenticate_user(username, password)
        if success:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error=message)
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            return render_template('register.html', error='Username and password are required')
        
        success, message = email_system.register_user(username, password)
        if success:
            return render_template('register.html', success=message)
        else:
            return render_template('register.html', error=message)
    
    return render_template('register.html')


@app.route('/dashboard')
def dashboard():
    """Main dashboard - inbox"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    messages = email_system.list_messages(username)
    
    return render_template('dashboard.html', username=username, messages=messages)


@app.route('/sent')
def sent():
    """Sent messages page"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    messages = email_system.list_sent_messages(username)
    
    return render_template('sent.html', username=username, messages=messages)


@app.route('/api/users')
def api_users():
    """API endpoint for getting all usernames (for autocomplete)"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    usernames = email_system.get_all_usernames()
    return jsonify({'users': usernames}), 200


@app.route('/send', methods=['GET', 'POST'])
def send_email():
    """Send email page"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        sender = session['username']
        recipients_str = request.form.get('recipient', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        
        # Handle image upload (if any)
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename:
                # Check file size (5MB limit)
                image_file.seek(0, os.SEEK_END)
                file_size = image_file.tell()
                image_file.seek(0)
                
                if file_size > 5 * 1024 * 1024:  # 5MB
                    return render_template('send.html', error='Image size must be less than 5MB', usernames=email_system.get_all_usernames())
                
                # Check if it's an image
                if not image_file.content_type.startswith('image/'):
                    return render_template('send.html', error='Please upload an image file', usernames=email_system.get_all_usernames())
                
                # Convert image to base64 and embed in message
                image_data = image_file.read()
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                image_tag = f'\n\n<img src="data:{image_file.content_type};base64,{image_base64}" alt="{image_file.filename}" style="max-width: 100%; height: auto;">'
                message += image_tag
        
        if not recipients_str or not message:
            return render_template('send.html', error='Recipient and message are required', usernames=email_system.get_all_usernames())
        
        # Parse multiple recipients (comma or semicolon separated)
        recipients = [r.strip() for r in recipients_str.replace(';', ',').split(',') if r.strip()]
        
        if not recipients:
            return render_template('send.html', error='At least one recipient is required', usernames=email_system.get_all_usernames())
        
        # Send to all recipients
        success_count = 0
        errors = []
        for recipient in recipients:
            success, msg = email_system.send_email(sender, recipient, message, subject)
            if success:
                success_count += 1
            else:
                errors.append(f"{recipient}: {msg}")
        
        if success_count > 0:
            if len(errors) > 0:
                return render_template('send.html', error=f'Sent to {success_count} recipient(s), but failed for: {", ".join(errors)}', usernames=email_system.get_all_usernames())
            return redirect(url_for('sent'))
        else:
            return render_template('send.html', error='Failed to send to all recipients: ' + '; '.join(errors), usernames=email_system.get_all_usernames())
    
    usernames = email_system.get_all_usernames()
    return render_template('send.html', usernames=usernames)


@app.route('/read/<int:message_id>')
def read_email(message_id):
    """Read and verify email"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    success, email_data, message = email_system.receive_email(username, message_id)
    
    if success and email_data:
        return render_template('read.html', email=email_data, message=message)
    else:
        return render_template('read.html', error=message)


@app.route('/reply/<int:message_id>', methods=['GET', 'POST'])
def reply_email(message_id):
    """Reply to an email"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    
    # Get original message for context
    success, original_email, _ = email_system.receive_email(username, message_id)
    if not success:
        return render_template('send.html', error="Original message not found")
    
    if request.method == 'POST':
        reply_message = request.form.get('message', '').strip()
        subject = request.form.get('subject', '').strip()
        
        # Handle image upload
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename:
                image_file.seek(0, os.SEEK_END)
                file_size = image_file.tell()
                image_file.seek(0)
                
                if file_size > 5 * 1024 * 1024:
                    return render_template('reply.html', original_email=original_email, error='Image size must be less than 5MB')
                
                if not image_file.content_type.startswith('image/'):
                    return render_template('reply.html', original_email=original_email, error='Please upload an image file')
                
                image_data = image_file.read()
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                image_tag = f'\n\n<img src="data:{image_file.content_type};base64,{image_base64}" alt="{image_file.filename}" style="max-width: 100%; height: auto;">'
                reply_message += image_tag
        
        if not reply_message:
            return render_template('reply.html', original_email=original_email, error='Message is required')
        
        success, msg = email_system.reply_email(message_id, username, reply_message, subject)
        if success:
            return redirect(url_for('dashboard'))
        else:
            return render_template('reply.html', original_email=original_email, error=msg)
    
    # Pre-fill subject
    original_subject = original_email.get('subject', '(No Subject)')
    if not original_subject.startswith('Re: '):
        reply_subject = f"Re: {original_subject}"
    else:
        reply_subject = original_subject
    
    return render_template('reply.html', original_email=original_email, reply_subject=reply_subject)


@app.route('/forward/<int:message_id>', methods=['GET', 'POST'])
def forward_email(message_id):
    """Forward an email"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    
    # Get original message for context
    success, original_email, _ = email_system.receive_email(username, message_id)
    if not success:
        return render_template('send.html', error="Original message not found")
    
    if request.method == 'POST':
        recipient = request.form.get('recipient', '').strip()
        forward_message = request.form.get('message', '').strip()
        subject = request.form.get('subject', '').strip()
        
        # Handle image upload
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename:
                image_file.seek(0, os.SEEK_END)
                file_size = image_file.tell()
                image_file.seek(0)
                
                if file_size > 5 * 1024 * 1024:
                    return render_template('forward.html', original_email=original_email, error='Image size must be less than 5MB')
                
                if not image_file.content_type.startswith('image/'):
                    return render_template('forward.html', original_email=original_email, error='Please upload an image file')
                
                image_data = image_file.read()
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                image_tag = f'\n\n<img src="data:{image_file.content_type};base64,{image_base64}" alt="{image_file.filename}" style="max-width: 100%; height: auto;">'
                forward_message += image_tag
        
        if not recipient:
            return render_template('forward.html', original_email=original_email, error='Recipient is required')
        
        success, msg = email_system.forward_email(message_id, username, recipient, forward_message, subject)
        if success:
            return redirect(url_for('dashboard'))
        else:
            return render_template('forward.html', original_email=original_email, error=msg)
    
    # Pre-fill subject
    original_subject = original_email.get('subject', '(No Subject)')
    if not original_subject.startswith('Fwd: ') and not original_subject.startswith('Fw: '):
        forward_subject = f"Fwd: {original_subject}"
    else:
        forward_subject = original_subject
    
    return render_template('forward.html', original_email=original_email, forward_subject=forward_subject)


@app.route('/logout')
def logout():
    """Logout"""
    session.pop('username', None)
    return redirect(url_for('login'))


# REST API endpoints
@app.route('/api/register', methods=['POST'])
def api_register():
    """API endpoint for user registration"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'}), 400
    
    success, message = email_system.register_user(username, password)
    return jsonify({'success': success, 'message': message}), 200 if success else 400


@app.route('/api/login', methods=['POST'])
def api_login():
    """API endpoint for user login"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'}), 400
    
    success, message = email_system.authenticate_user(username, password)
    if success:
        return jsonify({'success': True, 'message': message, 'username': username}), 200
    else:
        return jsonify({'success': False, 'message': message}), 401


@app.route('/api/send', methods=['POST'])
def api_send():
    """API endpoint for sending email"""
    data = request.get_json()
    sender = data.get('sender', '').strip()
    recipient = data.get('recipient', '').strip()
    message = data.get('message', '').strip()
    
    if not sender or not recipient or not message:
        return jsonify({'success': False, 'message': 'Sender, recipient, and message are required'}), 400
    
    success, msg = email_system.send_email(sender, recipient, message)
    return jsonify({'success': success, 'message': msg}), 200 if success else 400


@app.route('/api/inbox/<username>')
def api_inbox(username):
    """API endpoint for getting inbox"""
    messages = email_system.list_messages(username)
    return jsonify({'success': True, 'messages': messages}), 200


@app.route('/api/read/<username>/<int:message_id>')
def api_read(username, message_id):
    """API endpoint for reading email"""
    success, email_data, message = email_system.receive_email(username, message_id)
    if success:
        return jsonify({'success': True, 'email': email_data, 'message': message}), 200
    else:
        return jsonify({'success': False, 'message': message}), 404


if __name__ == '__main__':
    # Run on all interfaces (0.0.0.0) to allow network access
    # Change port if needed
    app.run(host='0.0.0.0', port=5000, debug=True)

