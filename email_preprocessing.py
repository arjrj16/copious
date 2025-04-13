import base64
from email import message_from_bytes
from googleapiclient.discovery import build
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import re
from bs4 import BeautifulSoup

# Define the Gmail API scope (read-only for email content)
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    service = build('gmail', 'v1', credentials=creds)
    return service

def fetch_email_raw(service, message_id):
    """
    Fetches an email in raw format given its message ID.
    """
    message = service.users().messages().get(userId='me', id=message_id, format='raw').execute()
    raw_data = message['raw']
    return raw_data

def decode_email(raw_email):
    """
    Decodes a base64 encoded raw email to a MIME message.
    """
    msg_bytes = base64.urlsafe_b64decode(raw_email.encode('ASCII'))
    mime_msg = message_from_bytes(msg_bytes)
    return mime_msg

def parse_mime_email(mime_msg):
    """
    Parses the MIME email message to extract key components.
    Returns a dictionary with subject, sender, and plain text body.
    """
    subject = mime_msg.get('Subject', 'No Subject')
    sender = mime_msg.get('From', 'Unknown Sender')
    
    body = ""
    # Check if the email is multipart
    if mime_msg.is_multipart():
        for part in mime_msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            # Ignore attachments and only get text parts
            if content_type == "text/plain" and "attachment" not in content_disposition:
                charset = part.get_content_charset() or "utf-8"
                body = part.get_payload(decode=True).decode(charset, errors="replace")
                break
    else:
        content_type = mime_msg.get_content_type()
        if content_type == "text/plain":
            charset = mime_msg.get_content_charset() or "utf-8"
            body = mime_msg.get_payload(decode=True).decode(charset, errors="replace")
    
    return {"subject": subject, "sender": sender, "body": body}

def clean_email_text(text):
    # Remove HTML tags if present
    soup = BeautifulSoup(text, 'html.parser')
    clean_text = soup.get_text()
    
    # Remove extra whitespace and newline characters
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    # Example: Remove common signature patterns (this is highly customizable)
    clean_text = re.sub(r'(?i)(--|Thanks,|Best regards,|Sincerely,).+', '', clean_text)
    
    return clean_text.strip()



if __name__ == "__main__":
    service = get_gmail_service()
    
    # For demonstration, retrieve the first email's message ID
    results = service.users().messages().list(userId='me', maxResults=1).execute()
    messages = results.get('messages', [])
    
    if not messages:
        print("No messages found.")
    else:
        message_id = messages[0]['id']
        raw_email = fetch_email_raw(service, message_id)
        mime_msg = decode_email(raw_email)
        print("Email Retrieved and Decoded Successfully")

    service = get_gmail_service()
    
    # Retrieve one email for demonstration purposes
    results = service.users().messages().list(userId='me', maxResults=1).execute()
    messages = results.get('messages', [])
    
    # if messages:
    #     message_id = messages[0]['id']
    #     raw_email = fetch_email_raw(service, message_id)
    #     mime_msg = decode_email(raw_email)
    #     parsed_email = parse_mime_email(mime_msg)
    #     print("Parsed Email Data:")
    #     print("Subject:", parsed_email['subject'])
    #     print("Sender:", parsed_email['sender'])
    #     print("Body Preview:", parsed_email['body'][:])  # Print first 200 characters
    # else:
    #     print("No emails to parse.")

    raw_text = "<html><body>Hello, please find the update below.<br><br>Thanks,<br>John Doe</body></html>"
    print(clean_email_text(raw_text))

