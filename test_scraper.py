
import requests
import json

# Test the scraper API
def test_scraper():
    url = "http://0.0.0.0:8080/scrape"
    
    # Test data
    test_data = {
        "niche": "restaurants",
        "location": "Mumbai",
        "email": "user@example.com"
    }
    
    print("Testing scraper API...")
    print(f"Sending POST request to: {url}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(url, json=test_data)
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

def test_quota():
    # Test quota endpoint
    email = "user@example.com"
    url = f"http://0.0.0.0:8080/quota/{email}"
    
    print(f"\nTesting quota for {email}...")
    try:
        response = requests.get(url)
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Test quota first
    test_quota()
    
    # Then test scraper
    test_scraper()
