import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Define the Gmail API scope (read-only in this example)
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    creds = None
    # token.json stores the user's access and refresh tokens.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no valid credentials available, then initiate the login flow.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Use the credentials.json file downloaded from Google Cloud Console
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for future use.
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    # Build the Gmail service instance
    service = build('gmail', 'v1', credentials=creds)
    return service

def list_emails(service):
    # Retrieve a list of message IDs from the user's mailbox (modify maxResults as necessary)
    results = service.users().messages().list(userId='me', maxResults=10).execute()
    messages = results.get('messages', [])
    if not messages:
        print("No messages found.")
    else:
        print("Message IDs:")
        for message in messages:
            print(message['subject'])

if __name__ == '__main__':
    service = get_gmail_service()
    list_emails(service)
