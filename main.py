
from app import app

if __name__ == '__main__':
    print("Starting Flask Lead Scraper API...")
    print("API will be available at: http://0.0.0.0:8080")
    print("\nEndpoints:")
    print("- POST /scrape - Main scraping endpoint")
    print("- GET /quota/<email> - Check quota status")
    print("- GET /health - Health check")
    
    app.run(host='0.0.0.0', port=8080, debug=True)
