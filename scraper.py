import requests
from bs4 import BeautifulSoup
import re
import os
from typing import List, Dict
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

def create_google_dork(niche: str, location: str) -> str:
    return (
        f'"{niche}" "{location}" site:.in OR site:.com '
        '-site:zomato.com -site:swiggy.com -site:justdial.com '
        '-site:tripadvisor.com -site:facebook.com -site:instagram.com '
        '-inurl:"/search" -inurl:"/tag/" -inurl:"/categories/" -intitle:"menu"'
    )

def is_real_business_site(url):
    domain = urlparse(url).netloc
    # Only filter out the most obvious non-business sites
    junk_sites = ['youtube.com', 'facebook.com', 'instagram.com', 'twitter.com', 'linkedin.com']
    return not any(junk in domain for junk in junk_sites)

def extract_contact_info(html_content: str, url: str) -> Dict:
    soup = BeautifulSoup(html_content, 'lxml')

    text = soup.get_text()

    common_spam_domains = ['example.com', 'test.com', 'dummy.com', 'noreply', 'support', 'info']

    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = list(set(
        email for email in re.findall(email_pattern, text)
        if not any(bad in email.lower() for bad in common_spam_domains)
    ))

    phone_patterns = [
        r'\+91[-\s]?[6-9]\d{9}',
        r'91[-\s]?[6-9]\d{9}',
        r'[6-9]\d{9}',
        r'\([0-9]{3}\)[-\s]?[0-9]{3}[-\s]?[0-9]{4}'
    ]

    phones = []
    for pattern in phone_patterns:
        phones.extend(re.findall(pattern, text))

    cleaned_phones = list(set([
        phone for phone in phones 
        if len(phone) >= 10 and not re.match(r'(\d)\1{5,}', phone)
    ]))

    social_pattern = r'https?://(?:www\.)?(?:facebook|instagram)\.com/[^\s<>"]*'
    social_links = list(set(re.findall(social_pattern, html_content)))

    return {
        'url': url,
        'emails': emails,
        'phones': cleaned_phones,
        'social_links': {
            'facebook': [link for link in social_links if 'facebook.com' in link],
            'instagram': [link for link in social_links if 'instagram.com' in link]
        }
    }

def scrape_url(url: str) -> Dict:
    try:
        if not is_real_business_site(url):
            print("Skipping social media site:", url)
            return {}

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=15)  # Increased timeout
        response.raise_for_status()

        # Extract contact info from any business site
        return extract_contact_info(response.text, url)

    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        # Still return the URL data even if scraping fails
        return {
            'url': url,
            'emails': [],
            'phones': [],
            'social_links': {},
            'error': str(e)
        }

def search_with_serper(query: str) -> List[str]:
    api_key = os.getenv('SERPER_API_KEY')
    if not api_key:
        raise ValueError("SERPER_API_KEY not found in environment variables")

    url = "https://google.serper.dev/search"
    payload = {
        'q': query,
        'num': 50  # Request more results to account for filtering
    }
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    data = response.json()
    urls = []
    if 'organic' in data:
        for result in data['organic']:
            if 'link' in result:
                urls.append(result['link'])

    return urls[:50]  # Return more URLs to process

def search_and_scrape(niche: str, location: str) -> List[Dict]:
    try:
        query = create_google_dork(niche, location)
        print(f"Searching for: {query}")

        urls = search_with_serper(query)
        print(f"Found {len(urls)} URLs")

        results = []
        target_count = 30
        
        for url in urls:
            if len(results) >= target_count:
                break
                
            print(f"Scraping: {url} (Result {len(results)+1}/{target_count})")
            scraped_data = scrape_url(url)
            
            # Accept any result that has data or even just a URL
            if scraped_data and scraped_data.get('url'):
                results.append(scraped_data)
            
        print(f"Collected {len(results)} results")
        return results[:target_count]  # Ensure exactly 30 or less

    except Exception as e:
        print(f"Error in search_and_scrape: {str(e)}")
        raise

