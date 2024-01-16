import base64
import logging
from lxml import etree
from dataclasses import dataclass, field
from decimal import Decimal
from jfkpay.gservices import gmail_login 

REIFFEISENBANK_TRANACTION_SUBJECT = 'Pohyb na účtě'

def get_mails():
  service = gmail_login()
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


@dataclass
class Transaction:
  ammount: Decimal
  currency: str
  category: str
  type: str
  account_dst: str
  account_dst_name: str
  account_src: str
  account_src_name: str
  message_for_reciever: str
  note: str
  variabilni_symbol: str
  konstantni_symbol: str
  specificky_symbol: str

  @classmethod
  def from_raiffeisenbank_msg_part(cls, part):
    doc = etree.HTML(part)
    trs = doc.xpath('//tbody//tr')
    parsed_table = {
      '\n'.join(tr.xpath('td[position()=1]/p/text()')).strip():
      '\n'.join(tr.xpath('td[position()=2]/p/text()')).strip() for tr in trs
    }
    
    ammount_raw, currency = parsed_table['Částka v měně účtu'].split(' ')
    ammount = Decimal(ammount_raw.replace('.', '').replace(',', '.'))

    account_src, _, account_src_name = parsed_table['Z účtu'].partition('\n')
    account_dst, _, account_dst_name = parsed_table['Na účet'].partition('\n')

    return cls(
      ammount = ammount,
      currency = currency,
      category = parsed_table['Kategorie pohybu'],
      type = parsed_table['Typ pohybu'],
      account_dst = account_dst,
      account_dst_name = account_dst,
      account_src = account_src,
      account_src_name = account_src_name,
      message_for_reciever = parsed_table.get('Zpráva pro příjemce'),
      note = parsed_table.get('Zpráva pro mne'),
      variabilni_symbol = parsed_table.get('Variabilní symbol'),
      konstantni_symbol = parsed_table.get('Konstantní symbol'),
      specificky_symbol = parsed_table.get('Specifický symbol')
    )


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
  email_data = msg['payload']['headers']
  subject = getval(email_data, 'Subject')
  name = getval(email_data, 'name')
  from_name = getval(email_data, 'From')
  return name, subject, from_name


def mark_read(msg):
  '''
  mark the message as read
  '''
  service = gmail_login()
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
    payment_info = list(Transaction.from_raiffeisenbank_msg_part(part) for part in parts)
    logging.info(f'{name}, {subject}, {from_name} {payment_info}')
    #mark_read(msg)
