#!/usr/bin/env python3
"""
One-time script to get OAuth 2.0 refresh token
Run this locally once to get your refresh token for Streamlit
Requires: pip install google-auth-oauthlib
"""

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_refresh_token():
    """Get refresh token by authenticating once"""
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES
    )
    
    # This will open browser for authentication
    credentials = flow.run_local_server(port=0)
    
    print("\n" + "="*60)
    print("✅ Authentication successful!")
    print("="*60)
    print("\nAdd these to your Streamlit secrets (.streamlit/secrets.toml):\n")
    print(f'gmail_client_id = "{credentials.client_id}"')
    print(f'gmail_client_secret = "{credentials.client_secret}"')
    print(f'gmail_refresh_token = "{credentials.refresh_token}"')
    print("\n" + "="*60)
    
    return credentials

if __name__ == "__main__":
    print("=== Get Gmail Refresh Token ===\n")
    print("This script will:")
    print("1. Open your browser for Gmail authentication")
    print("2. Generate a refresh token")
    print("3. Show you what to add to Streamlit secrets\n")
    
    try:
        get_refresh_token()
        print("\n✅ Done! Copy the values above to your secrets.toml file")
    except FileNotFoundError:
        print("\n❌ Error: credentials.json not found!")
        print("\nDownload OAuth 2.0 credentials from Google Cloud Console:")
        print("1. Go to APIs & Services > Credentials")
        print("2. Create OAuth 2.0 Client ID (Desktop app)")
        print("3. Download JSON as 'credentials.json'")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

