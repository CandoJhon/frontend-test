from flask import Flask, render_template, request, session, redirect, url_for, jsonify, flash
import os
import logging
import requests
from functools import wraps

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize IBM App ID - with error handling
try:
    from auth.app_id_auth import AppIDAuth
    app_id_auth = AppIDAuth(
        region=os.getenv("APPID_REGION", "us-east"),
        tenant_id=os.getenv("APPID_TENANT_ID"),
        client_id=os.getenv("APPID_CLIENT_ID"),
        secret=os.getenv("APPID_SECRET")
    )
    AUTH_ENABLED = True
    logger.info("IBM App ID authentication initialized")
except Exception as e:
    logger.error(f"Failed to initialize IBM App ID: {e}")
    AUTH_ENABLED = False

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AUTH_ENABLED:
            return jsonify({"error": "Authentication not configured"}), 500
        if 'access_token' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Main page"""
    try:
        user_info = session.get('user_info')
        is_authenticated = 'access_token' in session and AUTH_ENABLED
        
        # Try to render template
        return render_template('index.html', 
                             user_info=user_info, 
                             is_authenticated=is_authenticated,
                             auth_enabled=AUTH_ENABLED)
    except Exception as e:
        logger.error(f"Template error in index route: {str(e)}")
        # Fallback HTML if template fails
        user_info = session.get('user_info', {})
        is_authenticated = 'access_token' in session and AUTH_ENABLED
        
        return f"""
        <!DOCTYPE html>
        <html>
            <head>
                <title>Frontend App</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .status {{ background: #e8f5e8; padding: 10px; border-radius: 5px; margin: 10px 0; }}
                    .error {{ background: #ffe8e8; padding: 10px; border-radius: 5px; margin: 10px 0; }}
                    .btn {{ background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 5px; }}
                    a {{ color: #007bff; }}
                </style>
            </head>
            <body>
                <h1>Frontend Application with IBM App ID</h1>
                
                <div class="error">⚠️ Template Error: Using fallback HTML</div>
                
                {"<div class='status'>✅ Authentication: Enabled</div>" if AUTH_ENABLED else "<div class='error'>⚠️ Authentication: Not configured</div>"}
                
                {"<div class='status'>✅ Status: Logged in as " + str(user_info.get('email', user_info.get('name', 'User'))) + "</div>" if is_authenticated else "<div>ℹ️ Status: Not logged in</div>"}
                
                <h2>Navigation:</h2>
                <ul>
                    <li><a href="/health">Health Check</a></li>
                    <li><a href="/api/public">Public API</a></li>
                    <li><a href="/debug">Debug Info</a></li>
                    {"<li><a href='/login' class='btn'>Login with IBM App ID</a></li>" if not is_authenticated and AUTH_ENABLED else ""}
                    {"<li><a href='/profile' class='btn'>View Profile</a></li>" if is_authenticated else ""}
                    {"<li><a href='/logout' class='btn'>Logout</a></li>" if is_authenticated else ""}
                </ul>
                
                <h2>Error Details:</h2>
                <p>Template loading failed: {str(e)}</p>
                <p>This is a fallback page. Check if templates directory exists.</p>
            </body>
        </html>
        """, 200

@app.route('/login')
def login():
    """Login page - redirect to IBM App ID"""
    if not AUTH_ENABLED:
        return jsonify({"error": "Authentication not configured"}), 500
        
    if 'access_token' in session:
        return redirect(url_for('profile'))
    
    try:
        redirect_uri = os.getenv("APPID_REDIRECT_URI") or url_for('auth_callback', _external=True)
        login_url = app_id_auth.get_login_url(redirect_uri=redirect_uri)
        
        # Try to render template, fallback to simple HTML
        try:
            return render_template('login.html', login_url=login_url)
        except:
            return f"""
            <html>
                <head><title>Login</title></head>
                <body>
                    <h1>Login with IBM App ID</h1>
                    <p><a href="{login_url}">Click here to login</a></p>
                    <p><a href="/">Back to Home</a></p>
                </body>
            </html>
            """
    except Exception as e:
        logger.error(f"Error generating login URL: {e}")
        return jsonify({"error": str(e)}), 500

# In frontend app.py, modify the auth_callback route:
@app.route('/auth/callback')
def auth_callback():
    """Handle OAuth callback with detailed logging"""
    code = request.args.get('code')
    error = request.args.get('error')
    
    logger.info(f"Callback received - Code: {'Present' if code else 'Missing'}, Error: {error}")
    
    if error:
        logger.error(f"OAuth error: {error}")
        flash(f"Authentication error: {error}", 'error')
        return redirect(url_for('login'))
    
    if not code:
        logger.error("No authorization code received")
        flash("No authorization code received", 'error')
        return redirect(url_for('login'))
    
    try:
        backend_url = os.getenv('BACKEND_URL', 'http://localhost:8080')
        logger.info(f"Calling backend at: {backend_url}")
        
        # Call backend callback
        response = requests.get(f'{backend_url}/auth/callback', 
                              params={'code': code}, 
                              timeout=30)
        
        logger.info(f"Backend response status: {response.status_code}")
        logger.info(f"Backend response: {response.text[:200]}...")
        
        if response.status_code == 200:
            auth_data = response.json()
            logger.info(f"Backend auth successful: {auth_data.get('status')}")
            
            if auth_data.get('status') == 'success':
                session['access_token'] = auth_data['access_token']
                session['user_info'] = auth_data['user_info']
                logger.info("Session data stored successfully")
                flash('Successfully logged in!', 'success')
                return redirect(url_for('profile'))
            else:
                logger.error(f"Backend auth failed: {auth_data}")
                raise Exception(f"Backend returned: {auth_data}")
        else:
            logger.error(f"Backend request failed: {response.status_code}")
            raise Exception(f"Backend responded with {response.status_code}")
            
    except Exception as e:
        logger.error(f"Authentication callback failed: {str(e)}")
        flash(f"Authentication failed: {str(e)}", 'error')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """Logout user"""
    user_email = session.get('user_info', {}).get('email', 'Unknown')
    session.clear()
    logger.info(f"User logged out: {user_email}")
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    try:
        user_info = session.get('user_info')
        return render_template('profile.html', user_info=user_info)
    except Exception as e:
        logger.error(f"Error in profile route: {e}")
        user_info = session.get('user_info', {})
        return f"""
        <html>
            <head><title>Profile</title></head>
            <body>
                <h1>User Profile</h1>
                <p>Email: {user_info.get('email', 'No email')}</p>
                <p>Name: {user_info.get('name', 'No name')}</p>
                <p>User ID: {user_info.get('sub', 'No ID')}</p>
                <p><a href="/logout">Logout</a></p>
                <p><a href="/">Home</a></p>
            </body>
        </html>
        """

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
        response = requests.get(f'{backend_url}/api/protected', headers=headers, timeout=30)
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
        "authenticated": 'access_token' in session and AUTH_ENABLED,
        "auth_enabled": AUTH_ENABLED,
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
        'auth_provider': 'IBM App ID' if AUTH_ENABLED else 'Disabled',
        'auth_enabled': AUTH_ENABLED
    })

@app.route('/test')
def test_route():
    """Simple test route"""
    return jsonify({
        "message": "Test route working",
        "auth_enabled": AUTH_ENABLED,
        "templates_working": False  # We know templates aren't working
    })

@app.route('/debug')
def debug_info():
    """Debug information"""
    return jsonify({
        'auth_enabled': AUTH_ENABLED,
        'environment_vars': {
            'APPID_REGION': os.getenv('APPID_REGION', 'Not set'),
            'APPID_TENANT_ID': 'Set' if os.getenv('APPID_TENANT_ID') else 'Not set',
            'APPID_CLIENT_ID': 'Set' if os.getenv('APPID_CLIENT_ID') else 'Not set',
            'APPID_SECRET': 'Set' if os.getenv('APPID_SECRET') else 'Not set',
            'BACKEND_URL': os.getenv('BACKEND_URL', 'Not set')
        },
        'session_data': {
            'authenticated': 'access_token' in session,
            'user_email': session.get('user_info', {}).get('email', 'Not logged in')
        }
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Page not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    try:
        logger.error(f"Internal error: {str(error)}")
        return jsonify({
            "error": "Internal server error", 
            "message": "Something went wrong",
            "status": 500
        }), 500
    except Exception as e:
        # Last resort error handling
        return f"<html><body><h1>500 Internal Server Error</h1><p>Error: {str(e)}</p></body></html>", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask app on port {port}")
    logger.info(f"Authentication enabled: {AUTH_ENABLED}")
    app.run(host='0.0.0.0', port=port, debug=False)