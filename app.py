
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from scraper import search_and_scrape
from google_sheets import save_to_sheet
from quota_manager import check_quota, increment_usage

load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/scrape', methods=['POST'])
def scrape_endpoint():
    try:
        data = request.get_json()
        
        if not data or 'niche' not in data or 'location' not in data:
            return jsonify({'error': 'Missing niche or location in request'}), 400
        
        # Check if email is provided for quota management
        email = data.get('email')
        if email:
            can_search, message = check_quota(email)
            if not can_search:
                return jsonify({'error': message}), 429
        
        niche = data['niche']
        location = data['location']
        
        # Search and scrape
        scraped_data = search_and_scrape(niche, location)
        
        if not scraped_data:
            return jsonify({'error': 'No data found'}), 404
        
        # Save to Google Sheets
        sheet_url = save_to_sheet(scraped_data, niche, location)
        
        # Increment usage count if email provided
        if email:
            increment_usage(email)
        
        return jsonify({
            'status': 'success',
            'sheet_url': sheet_url,
            'results_count': len(scraped_data)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'message': 'Lead Scraper API',
        'version': '1.0',
        'endpoints': {
            'POST /scrape': 'Main scraping endpoint - requires niche, location, and optional email',
            'GET /quota/<email>': 'Check quota status for user',
            'GET /health': 'Health check endpoint'
        },
        'example_usage': {
            'scrape': {
                'method': 'POST',
                'url': '/scrape',
                'body': {
                    'niche': 'restaurants',
                    'location': 'Mumbai', 
                    'email': 'user@example.com'
                }
            }
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

@app.route('/quota/<email>', methods=['GET'])
def get_quota_status(email):
    """Get user's quota status"""
    try:
        from quota_manager import get_user_plan
        plan = get_user_plan(email)
        can_search, message = check_quota(email)
        
        return jsonify({
            'email': email,
            'plan': plan,
            'can_search': can_search,
            'message': message
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
