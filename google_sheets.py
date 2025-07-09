
import gspread
from google.oauth2.service_account import Credentials
import os
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv
import time

load_dotenv()

def setup_google_sheets():
    """Setup Google Sheets client"""
    
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
    client = gspread.authorize(creds)
    return client

def make_spreadsheet_public(spreadsheet):
    """Make spreadsheet publicly accessible"""
    try:
        # Method 1: Share with anyone who has the link
        spreadsheet.share('', perm_type='anyone', role='writer')
        print(f"✓ Spreadsheet made publicly accessible (method 1)")
        return True
    except Exception as e1:
        print(f"Method 1 failed: {e1}")
        try:
            # Method 2: Alternative sharing
            spreadsheet.share(None, perm_type='anyone', role='writer')
            print(f"✓ Spreadsheet made publicly accessible (method 2)")
            return True
        except Exception as e2:
            print(f"Method 2 failed: {e2}")
            try:
                # Method 3: Use permissions directly
                spreadsheet.share(email_address='', perm_type='anyone', role='writer')
                print(f"✓ Spreadsheet made publicly accessible (method 3)")
                return True
            except Exception as e3:
                print(f"All sharing methods failed: {e3}")
                return False

def extract_title_from_url(url: str) -> str:
    """Extract a simple title from URL"""
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        return domain.replace('www.', '').replace('.com', '').replace('.in', '').title()
    except:
        return "Unknown"

def save_to_sheet(scraped_data: List[Dict], niche: str, location: str) -> str:
    """Save scraped data to Google Sheet and return sheet URL"""
    try:
        client = setup_google_sheets()
        
        # Get or create spreadsheet
        sheet_name = os.getenv('GOOGLE_SHEET_NAME', 'Web Scraper Results')
        
        try:
            spreadsheet = client.open_by_key('1iSTfk87NFPfQXzRY8RyB7CQzqBOnU5-MFeTxLeFoXSQ')
        except gspread.SpreadsheetNotFound:
            spreadsheet = client.create(sheet_name)
            # Make spreadsheet publicly accessible
            success = make_spreadsheet_public(spreadsheet)
            if not success:
                print("⚠️  Manual sharing required:")
                print(f"   1. Open: {spreadsheet.url}")
                print(f"   2. Click 'Share' → 'Anyone with the link can view'")
                print(f"   3. Copy the shareable link")
        
        # Create new worksheet for this search
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        worksheet_name = f"{niche}_{location}_{timestamp}"
        
        try:
            worksheet = spreadsheet.add_worksheet(
                title=worksheet_name,
                rows=len(scraped_data) + 20,
                cols=10
            )
        except Exception:
            # If worksheet creation fails, use the first sheet
            worksheet = spreadsheet.sheet1
            worksheet.clear()
        
        # Prepare headers - matching old format
        headers = [
            'URL',
            'Title', 
            'Emails',
            'Phone Numbers',
            'Facebook Profiles',
            'Instagram Profiles', 
            'Scraped At',
            'Status'
        ]
        
        # Add headers
        worksheet.append_row(headers)
        
        # Add data rows
        scraped_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for item in scraped_data:
            # Extract social links properly
            social_links = item.get('social_links', {})
            facebook_profiles = []
            instagram_profiles = []
            
            if isinstance(social_links, dict):
                facebook_profiles = social_links.get('facebook', [])
                instagram_profiles = social_links.get('instagram', [])
            elif isinstance(social_links, list):
                # Filter by platform if it's a simple list
                facebook_profiles = [link for link in social_links if 'facebook.com' in link]
                instagram_profiles = [link for link in social_links if 'instagram.com' in link]
            
            # Generate title from URL
            title = extract_title_from_url(item['url'])
            
            # Determine status
            status = 'Error' if 'error' in item else 'Success'
            
            row = [
                item['url'],
                title,
                ', '.join(item.get('emails', [])) if item.get('emails') else '',
                ', '.join(item.get('phones', [])) if item.get('phones') else '',
                ', '.join(facebook_profiles) if facebook_profiles else '',
                ', '.join(instagram_profiles) if instagram_profiles else '',
                scraped_time,
                status
            ]
            worksheet.append_row(row)
        
        # Add summary section - matching old format
        worksheet.append_row([])  # Empty row
        worksheet.append_row(['Summary'])
        worksheet.append_row(['Search Query', f'"{niche}" "{location}"'])
        worksheet.append_row(['Total URLs Scraped', len(scraped_data)])
        
        # Calculate totals
        total_emails = sum(len(item.get('emails', [])) for item in scraped_data)
        total_phones = sum(len(item.get('phones', [])) for item in scraped_data)
        
        total_facebook = 0
        total_instagram = 0
        for item in scraped_data:
            social_links = item.get('social_links', {})
            if isinstance(social_links, dict):
                total_facebook += len(social_links.get('facebook', []))
                total_instagram += len(social_links.get('instagram', []))
        
        worksheet.append_row(['Total Emails Found', total_emails])
        worksheet.append_row(['Total Phone Numbers Found', total_phones])
        worksheet.append_row(['Total Facebook Profiles Found', total_facebook])
        worksheet.append_row(['Total Instagram Profiles Found', total_instagram])
        
        # Format the worksheet - matching old format
        try:
            # Format headers with blue background
            worksheet.format('A1:H1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9}
            })
            
            # Format summary section
            summary_start_row = len(scraped_data) + 3
            worksheet.format(f'A{summary_start_row}:B{summary_start_row}', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            })
            
            # Auto-resize columns
            try:
                worksheet.columns_auto_resize(0, 7)
            except:
                # Fallback: set specific column widths
                pass
                
        except Exception as e:
            print(f"Column formatting warning: {e}")
        
        return spreadsheet.url
        
    except Exception as e:
        print(f"Error saving to Google Sheets: {str(e)}")
        raise
