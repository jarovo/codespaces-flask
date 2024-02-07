import datetime
import base64
import logging

from typing import Any, TypeVar, Iterable
from contextlib import ExitStack

from email.mime.text import MIMEText
from jfkpay.gservices import gmail_login, build_service, get_credentials
from jfkpay.model import (
    Person,
    Transaction,
    Voucher,
    ResourceManager,
    CUSTOMER_NOTIFIED,
    BUSINESS_NOTIFIED,
)
from jfkpay import model

REIFFEISENBANK_TRANACTION_SUBJECT = "Pohyb na účtě"


Message = TypeVar("Message")


def get_mails(service, userId: str) -> Message:
    results = (
        service.users().messages().list(userId=userId, labelIds=["INBOX"]).execute()
    )
    #      userId=userId, labelIds=['INBOX'], q="is:unread").execute()
    messages = results.get("messages", [])
    if not messages:
        logging.info("No new messages.")
    else:
        message_count = 0
        for message in messages:
            yield service.users().messages().get(
                userId=userId, id=message["id"]
            ).execute()


def read_parts(msg: Message):
    parts = msg["payload"].get("parts", [])
    for part in parts:
        content_type = getval(part["headers"], "Content-Type")
        if content_type != "text/html; charset=utf-8":
            logging.debug(f"{content_type:}")
            continue
        data = part["body"]["data"]
        byte_code = base64.urlsafe_b64decode(data)
        yield byte_code.decode("utf-8")


def read_mail(msg: Message):
    email_data = msg["payload"]["headers"]
    subject = getval(email_data, "Subject")
    name = getval(email_data, "name")
    from_name = getval(email_data, "From")
    return name, subject, from_name


def mark_read(service, msg: Message):
    """
    mark the message as read
    """
    service.users().messages().modify(
        userId="me", id=msg["id"], body={"removeLabelIds": ["UNREAD"]}
    ).execute()


def filter_by_subject(msgs: Iterable[Message], subject):
    for msg in msgs:
        if getval(msg["payload"]["headers"], "Subject") == subject:
            yield msg


def getval(headers, name):
    return "".join(v["value"] for v in headers if v["name"] == name)


def send_email(service, subject, recipient, text):
    credentials = get_credentials("", "")
    service = build_service(credentials)

    message = MIMEText(text)
    message["to"] = recipient
    message["subject"] = subject
    create_message = {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}
    message = (
        service.users().messages().send(userId="me", body=create_message).execute()
    )
    logging.info(f'Sent message {subject} to {recipient} Message Id: {message["id"]}')


def subscribe_for_emails(service):
    request = {
        "labelIds": ["INBOX"],
        "topicName": "projects/myproject/topics/mytopic",
        "labelFilterBehavior": "INCLUDE",
    }
    service.users().watch(userId="me", body=request).execute()


class PaymentPreconditionFailed(Exception):
    pass


def voucher_paid(
    customer: Person,
    business_representative: Person,
    voucher: Voucher,
    transaction: Transaction,
    message: Any,
):
    prev_state = None
    new_state = None

    def cleanup_message():
        """
        Set the messages to state indicating they have been processed.
        """
        new_state.execute()

    with ExitStack() as stack:
        stack.callback(cleanup_message)

        new_state = (
            message.service.users()
            .messages()
            .modify(
                userId="me",
                id=self.message["id"],
                body={"addLabelIds": [CUSTOMER_NOTIFIED, BUSINESS_NOTIFIED]},
            )
        )

        def check_resource_ok(resources):
            voucher, transaction = resources
            if voucher.payment_datetime:
                raise PaymentPreconditionFailed(
                    f"Voucher payment_datetime already set to {voucher.payment_datetime}"
                )

            if transaction.payment_datetime:
                raise PaymentPreconditionFailed(
                    f"Transaction payment_datetime already set to {transaction.payment_datetime}"
                )

            if voucher.amount != transaction.amount:
                raise PaymentPreconditionFailed(
                    f"Amount mismatch: {voucher:} {transaction:}"
                )

        check_resource_ok()

        def cleanup_voucher():
            voucher.payment_datetime = None
            voucher.transaction = None

        stack.callback(cleanup_voucher)

        def pay_the_voucher():
            voucher.payment_datetime = datetime.now()
            voucher.transaction = transaction
            send_email(
                "Děkujeme, platba za voucher {voucher} přijata.",
                customer,
                "Děkujeme za Váš nákup voucheru {voucher}.",
            )

            send_email(
                "Voucher {voucher} zaplacen.",
                business_representative,
                "Zákazníkovi {customer} bylo posláno oznámení o platbě voucheru {voucher}."
                "Transakce: {transaction}",
            )

        pay_the_voucher()
        stack.pop_all()


def load_transactions_infos(service):
    found_messages = list(
        filter_by_subject(get_mails(service, "me"), REIFFEISENBANK_TRANACTION_SUBJECT)
    )
    for msg in found_messages:
        name, subject, from_name = read_mail(msg)
        parts = list(read_parts(msg))
        for part in parts:
            yield Transaction.from_raiffeisenbank_msg_part(part)


def process_payments(payment_infos: Iterable[Transaction]):
    for payment_info in payment_infos:
        if payment_info.voucher_uuid:
            voucher = Voucher.get(payment_info.voucher_uuid)
