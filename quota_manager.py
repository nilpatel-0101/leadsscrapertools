
import json
import os
from datetime import datetime, date
from typing import Tuple

USERS_FILE = 'users.json'

# Plan configurations
PLANS = {
    'Free Trial': {'quota': 5, 'period': 'daily'},
    'Starter': {'quota': 30, 'period': 'monthly'},
    'Pro': {'quota': 100, 'period': 'monthly'},
    'Agency': {'quota': 300, 'period': 'monthly'},
    'Ultimate': {'quota': 100, 'period': 'daily'}
}

def load_users() -> dict:
    """Load users data from JSON file"""
    if not os.path.exists(USERS_FILE):
        return {}
    
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_users(users_data: dict) -> None:
    """Save users data to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users_data, f, indent=2)

def get_user_plan(email: str) -> str:
    """Get user's plan name"""
    users = load_users()
    if email not in users:
        return 'Free Trial'  # Default plan
    return users[email].get('plan', 'Free Trial')

def reset_if_needed(email: str) -> None:
    """Reset usage if quota period has passed"""
    users = load_users()
    
    if email not in users:
        # Create new user with default plan
        users[email] = {
            'plan': 'Free Trial',
            'used': 0,
            'quota': PLANS['Free Trial']['quota'],
            'last_reset': str(date.today()),
            'created_at': str(datetime.now())
        }
        save_users(users)
        return
    
    user = users[email]
    plan_name = user.get('plan', 'Free Trial')
    plan_config = PLANS.get(plan_name, PLANS['Free Trial'])
    
    last_reset = user.get('last_reset', str(date.today()))
    current_date = str(date.today())
    
    should_reset = False
    
    if plan_config['period'] == 'daily':
        # Reset daily
        if last_reset != current_date:
            should_reset = True
    elif plan_config['period'] == 'monthly':
        # Reset monthly
        try:
            last_reset_date = datetime.strptime(last_reset, '%Y-%m-%d').date()
            current_date_obj = date.today()
            
            if (last_reset_date.year != current_date_obj.year or 
                last_reset_date.month != current_date_obj.month):
                should_reset = True
        except ValueError:
            should_reset = True
    
    if should_reset:
        user['used'] = 0
        user['last_reset'] = current_date
        user['quota'] = plan_config['quota']
        save_users(users)

def check_quota(email: str) -> Tuple[bool, str]:
    """
    Check if user can perform a search
    Returns (can_search: bool, message: str)
    """
    reset_if_needed(email)
    
    users = load_users()
    user = users.get(email, {})
    
    plan_name = user.get('plan', 'Free Trial')
    used = user.get('used', 0)
    quota = user.get('quota', PLANS['Free Trial']['quota'])
    
    if used >= quota:
        return False, f"Quota exceeded. Please upgrade your plan. Current plan: {plan_name} ({used}/{quota} searches used)"
    
    remaining = quota - used
    return True, f"Search allowed. {remaining} searches remaining on {plan_name} plan"

def increment_usage(email: str) -> None:
    """Increment user's usage count by 1"""
    users = load_users()
    
    if email not in users:
        reset_if_needed(email)  # This will create the user
        users = load_users()
    
    users[email]['used'] = users[email].get('used', 0) + 1
    save_users(users)

def update_user_plan(email: str, new_plan: str) -> bool:
    """Update user's plan"""
    if new_plan not in PLANS:
        return False
    
    users = load_users()
    
    if email not in users:
        reset_if_needed(email)  # Create user first
        users = load_users()
    
    # Update plan and reset quota
    users[email]['plan'] = new_plan
    users[email]['quota'] = PLANS[new_plan]['quota']
    users[email]['used'] = 0  # Reset usage when upgrading
    users[email]['last_reset'] = str(date.today())
    
    save_users(users)
    return True

# Utility function for testing
def get_user_status(email: str) -> dict:
    """Get complete user status"""
    users = load_users()
    user = users.get(email, {})
    
    plan_name = user.get('plan', 'Free Trial')
    used = user.get('used', 0)
    quota = user.get('quota', PLANS['Free Trial']['quota'])
    
    return {
        'email': email,
        'plan': plan_name,
        'used': used,
        'quota': quota,
        'remaining': quota - used,
        'last_reset': user.get('last_reset', 'Never')
    }
