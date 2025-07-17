from flask import Flask, render_template, jsonify, request
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Frontend application is running'
    })

@app.route('/api/data')
def get_data():
    """API endpoint to provide data to frontend"""
    sample_data = {
        'message': 'Hello from Flask API!',
        'items': [
            {'id': 1, 'name': 'Item 1', 'description': 'First item'},
            {'id': 2, 'name': 'Item 2', 'description': 'Second item'},
            {'id': 3, 'name': 'Item 3', 'description': 'Third item'}
        ],
        'timestamp': '2025-07-17'
    }
    return jsonify(sample_data)

@app.route('/api/submit', methods=['POST'])
def submit_data():
    """API endpoint to handle form submissions"""
    try:
        data = request.get_json()
        logger.info(f"Received data: {data}")
        
        # Process the data here (save to database, etc.)
        response = {
            'status': 'success',
            'message': 'Data received successfully',
            'received_data': data
        }
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to process data'
        }), 400

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)