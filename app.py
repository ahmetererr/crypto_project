"""
Flask web server for Secure Email System
Allows remote access to the email system via REST API and web interface
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from email_system import EmailSystem
import os

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


@app.route('/send', methods=['GET', 'POST'])
def send_email():
    """Send email page"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        sender = session['username']
        recipient = request.form.get('recipient', '').strip()
        message = request.form.get('message', '').strip()
        
        if not recipient or not message:
            return render_template('send.html', error='Recipient and message are required')
        
        success, msg = email_system.send_email(sender, recipient, message)
        if success:
            return render_template('send.html', success=msg)
        else:
            return render_template('send.html', error=msg)
    
    return render_template('send.html')


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

