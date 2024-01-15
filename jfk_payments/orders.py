import base64
import logging
import os.path
from lxml import etree

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

REIFFEISENBANK_TRANACTION_SUBJECT = 'Pohyb na účtě'

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly",
          "https://www.googleapis.com/auth/gmail.modify"]

service = None


def login():
  """Shows basic usage of the Gmail API.
  Lists the user's Gmail labels.
  """
  global service
  creds = None

  if service:
    return service

  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  service = build("gmail", "v1", credentials=creds)
  return service


def get_mails():
  service = login()
  try:
    # Call the Gmail API

    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread").execute()
    messages = results.get('messages',[]);
    if not messages:
        print('No new messages.')
    else:
      message_count = 0
      for message in messages:
          yield service.users().messages().get(userId='me', id=message['id']).execute()
  except Exception as error:
    print(f"An error occurred: {error}")


def peck_out_values_raiffeisenbank_part(part):
  doc = etree.HTML(part)
  trs = doc.xpath('//tbody//tr')
  yield {'\n'.join(tr.xpath('td[position()=1]/p/text()')).strip(): '\n'.join(tr.xpath('td[position()=2]/p/text()')).strip() for tr in trs}


def read_parts(msg):
  parts = msg['payload'].get('parts', [])
  for part in parts:
      content_type = getval(part['headers'], 'Content-Type')
      if content_type != 'text/html; charset=utf-8':
        logging.debug(f'{content_type:}')
        continue
      data = part['body']['data']
      byte_code = base64.urlsafe_b64decode(data)
      yield byte_code.decode("utf-8")


def read_mail(msg):
  service = login()
  email_data = msg['payload']['headers']
  subject = getval(email_data, 'Subject')
  name = getval(email_data, 'name')
  from_name = getval(email_data, 'From')
  return name, subject, from_name


def mark_read(msg):
  '''
  mark the message as read
  '''
  service.users().messages().modify(userId='me', id=msg['id'], body={'removeLabelIds': ['UNREAD']}).execute()


def filter_by_subject(msgs, subject):
  for msg in msgs:
    if getval(msg['payload']['headers'], 'Subject') == subject:
      yield msg


def getval(headers, name):
  return ''.join(v['value'] for v in headers if v['name'] == name)


def main():
  logging.basicConfig(level=logging.INFO)
  found_messages = list(filter_by_subject(get_mails(), REIFFEISENBANK_TRANACTION_SUBJECT))
  for msg in found_messages:
    name, subject, from_name = read_mail(msg)
    parts = list(read_parts(msg))
    payment_info = list(list(peck_out_values_raiffeisenbank_part(part)) for part in parts)
    logging.info(f'{name}, {subject}, {from_name} {payment_info}')
    #mark_read(msg)
