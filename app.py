from flask import Flask, render_template, request, session, redirect, url_for, jsonify, flash
import os
import logging
import requests
from functools import wraps
from auth.app_id_auth import AppIDAuth

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize IBM App ID
app_id_auth = AppIDAuth(
    region=os.getenv("APPID_REGION", "us-east"),
    tenant_id=os.getenv("APPID_TENANT_ID"),
    client_id=os.getenv("APPID_CLIENT_ID"),
    secret=os.getenv("APPID_SECRET")
)

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_token' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Main page"""
    user_info = session.get('user_info')
    is_authenticated = 'access_token' in session
    return render_template('index.html', user_info=user_info, is_authenticated=is_authenticated)

@app.route('/login')
def login():
    """Login page - redirect to IBM App ID"""
    if 'access_token' in session:
        return redirect(url_for('profile'))
    
    try:
        redirect_uri = os.getenv("APPID_REDIRECT_URI") or url_for('auth_callback', _external=True)
        login_url = app_id_auth.get_login_url(redirect_uri=redirect_uri)
        return render_template('login.html', login_url=login_url)
    except Exception as e:
        logger.error(f"Error generating login URL: {e}")
        flash(f"Error: {e}", 'error')
        return render_template('login.html', error=str(e))

@app.route('/auth/callback')
def auth_callback():
    """Handle OAuth callback from IBM App ID"""
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        flash(f"Authentication error: {error}", 'error')
        return redirect(url_for('login'))
    
    if not code:
        flash("No authorization code received", 'error')
        return redirect(url_for('login'))
    
    try:
        # Exchange code for tokens
        redirect_uri = os.getenv("APPID_REDIRECT_URI") or url_for('auth_callback', _external=True)
        tokens = app_id_auth.exchange_code_for_tokens(code, redirect_uri=redirect_uri)
        
        # Get user info
        user_info = app_id_auth.get_user_info(tokens['access_token'])
        
        # Store in session
        session['access_token'] = tokens['access_token']
        session['refresh_token'] = tokens.get('refresh_token')
        session['user_info'] = user_info
        
        flash('Successfully logged in!', 'success')
        logger.info(f"User logged in: {user_info.get('email')}")
        
        return redirect(url_for('profile'))
        
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        flash(f"Authentication failed: {e}", 'error')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """Logout user"""
    user_email = session.get('user_info', {}).get('email', 'Unknown')
    session.clear()
    flash('Successfully logged out!', 'info')
    logger.info(f"User logged out: {user_email}")
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    user_info = session.get('user_info')
    return render_template('profile.html', user_info=user_info)

@app.route('/api/protected')
@login_required
def protected_api():
    """Protected API endpoint"""
    access_token = session.get('access_token')
    user_info = session.get('user_info')
    
    # Call backend API with token
    backend_url = os.getenv('BACKEND_URL', 'http://localhost:8080')
    headers = {'Authorization': f'Bearer {access_token}'}
    
    try:
        response = requests.get(f'{backend_url}/api/protected', headers=headers, timeout=10)
        if response.status_code == 200:
            backend_data = response.json()
        else:
            backend_data = {"error": f"Backend responded with {response.status_code}"}
    except Exception as e:
        backend_data = {"error": str(e)}
    
    return jsonify({
        "message": "Frontend protected endpoint",
        "user": user_info,
        "backend_data": backend_data
    })

@app.route('/api/public')
def public_api():
    """Public API endpoint"""
    return jsonify({
        "message": "This is a public endpoint",
        "authenticated": 'access_token' in session,
        "data": [
            {"id": 1, "title": "Public Item 1"},
            {"id": 2, "title": "Public Item 2"}
        ]
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Frontend application is running',
        'auth_provider': 'IBM App ID'
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal error: {error}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)