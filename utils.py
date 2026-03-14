# utils.py
import os
import json
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import shutil
from datetime import datetime

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_PATH = "secrets/credentials.json"
TOKEN_PATH = "secrets/token.json"
PASSWORDS_PATH = "secrets/broker_passwords.json"

def connect_gmail():
    """Authenticates and returns the Gmail service."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def download_attachments(service, query, save_dir):
    """Searches for emails matching the query and downloads PDF attachments."""
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])
    downloaded_files = []

    if not messages:
        print(f"No messages found for query: {query}")
        return downloaded_files

    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        
        for part in msg['payload'].get('parts', []):
            if part['filename'] and part['filename'].endswith('.pdf'):
                if 'data' in part['body']:
                    data = part['body']['data']
                else:
                    att_id = part['body']['attachmentId']
                    att = service.users().messages().attachments().get(
                        userId='me', messageId=message['id'], id=att_id).execute()
                    data = att['data']
                
                file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
                filepath = os.path.join(save_dir, part['filename'])
                
                with open(filepath, 'wb') as f:
                    f.write(file_data)
                
                print(f"Downloaded: {filepath}")
                downloaded_files.append(filepath)
                
    return downloaded_files

def get_broker_password(broker_name):
    """Reads the broker password from the secrets file."""
    try:
        with open(PASSWORDS_PATH, "r") as f:
            passwords = json.load(f)
            return passwords.get(broker_name)
    except FileNotFoundError:
        print(f"Error: {PASSWORDS_PATH} not found.")
        return None

def cleanup_downloads():
    """Moves downloaded files to a structured archive folder based on broker and date."""
    print("\n--- Starting Cleanup (Archiving) ---")
    
    download_dir = "downloads"
    # Using a raw string (r"") to safely handle Windows backslashes
    base_archive_dir = r"C:\Users\Pdogg Windows10\Desktop\Investment Information\Stocks"
    
    # Map your local download folders to your official desktop folder names
    broker_mapping = {
        "kotak": "Kotak Securities",
        "angelone": "Angel One",
        "groww": "Groww"  # Ready for when you add it
    }
    
    if not os.path.exists(download_dir):
        print(f"Directory '{download_dir}' does not exist. Nothing to clean.")
        return

    for root, dirs, files in os.walk(download_dir):
        for file in files:
            source_path = os.path.join(root, file)
            
            # Determine broker from the current folder name (e.g., 'kotak' or 'angelone')
            broker_folder = os.path.basename(root).lower()
            
            if broker_folder not in broker_mapping:
                print(f"Skipping {file}: Unknown broker folder '{broker_folder}'")
                continue
            
            official_broker_name = broker_mapping[broker_folder]
            
            # Extract Date based on the broker's specific naming convention
            try:
                if broker_folder == "kotak":
                    # CN_20260309_W8RHY_MER.pdf -> 20260309
                    raw_date = file.split('_')[1]
                    dt_obj = datetime.strptime(raw_date, '%Y%m%d')
                    
                elif broker_folder == "angelone":
                    # CN_S592652_09032026.pdf -> 09032026
                    raw_date = file.split('_')[2].replace('.pdf', '')
                    dt_obj = datetime.strptime(raw_date, '%d%m%Y')
                    
                else:
                    print(f"Date logic not set up for {broker_folder}. Skipping.")
                    continue
                
                # Format the year (2026) and full month name (March)
                year_str = dt_obj.strftime('%Y')
                month_str = dt_obj.strftime('%B')
                
            except Exception as e:
                print(f"Could not parse date from {file}. Error: {e}")
                continue
            
            # Construct the final destination path
            # Result: C:\...\Stocks\Angel One\Contract Notes\2026\March
            dest_dir = os.path.join(base_archive_dir, official_broker_name, "Contract Notes", year_str, month_str)
            
            # Create the Year\Month folders if they don't exist yet
            os.makedirs(dest_dir, exist_ok=True)
            
            dest_path = os.path.join(dest_dir, file)
            
            try:
                # Move the file and overwrite if it already exists in the archive
                shutil.move(source_path, dest_path)
                print(f"Successfully archived: {file} -> {dest_dir}")
            except Exception as e:
                print(f"Failed to move {file}. Error: {e}")
                
    print("Cleanup complete.")