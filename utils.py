# utils.py
import os
import json
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

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