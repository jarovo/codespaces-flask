import logging
from datetime import datetime
from copy import deepcopy
from uuid import uuid4
from contextlib import contextmanager, AbstractContextManager, ExitStack
import base64

from enum import Enum, auto
from lxml import etree

from abc import ABC
from typing import Any, List, TypeVar, Generic, Optional


from dataclasses import dataclass, field, InitVar, KW_ONLY, asdict
from decimal import Decimal

import base64
import os

from hashlib import blake2b
from hmac import compare_digest

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import jfkpay.config
from flask import jsonify, abort

ENCODING = "utf-8"


class ResourceManager(AbstractContextManager):
    def __init__(self, acquire_resource, release_resource, check_resource_ok=None):
        self.acquire_resource = acquire_resource
        self.release_resource = release_resource
        if check_resource_ok is None:

            def check_resource_ok(resource):
                return True

        self.check_resource_ok = check_resource_ok

    @contextmanager
    def _cleanup_on_error(self):
        with ExitStack() as stack:
            stack.push(self)
            yield
            # The validation check passed and didn't raise an exception
            # Accordingly, we want to keep the resource, and pass it
            # back to our caller
            stack.pop_all()

    def __enter__(self):
        resource = self.acquire_resource()
        with self._cleanup_on_error():
            if not self.check_resource_ok(resource):
                msg = "Failed validation for {!r}"
                raise RuntimeError(msg.format(resource))
        return resource

    def __exit__(self, *exc_details):
        # We don't need to duplicate any of our resource release logic
        self.release_resource()


T = TypeVar("T")


@dataclass(kw_only=True)
class Database(Generic[T]):
    _data: dict[T] = field(default_factory=dict)

    def get_or_404(self, uuid) -> T:
        if None is self._data.get(str(uuid)):
            abort(404)

    def save(self, resource: T):
        self._data[str(resource.uuid)] = resource

    def all(self):
        return self._data.values()


class VouchersDB(Database):
    pass


class TransactionsDB(Database):
    pass


class BusinessesDB(Database):
    pass


@dataclass
class Mongodata(ABC):
    _: KW_ONLY
    _id: Optional[int] = None

    @property
    def dict(self):
        result = asdict(self)
        result.pop("_id")
        return result


@dataclass(kw_only=True)
class Saveable(ResourceManager, Mongodata, Generic[T]):
    uuid: str = field(default_factory=uuid4)

    # def __post_init__(self, database):
    #    if self.j is None and database is not None:
    #        self.j = database.lookup('j')

    #   ResourceManager.__init__(self.get, self.save)

    def load(self) -> T:
        resource = self.db.get_or_404(self.uuid)
        logging.info("got {resource}")
        return resource

    def save(self):
        self.db.save(self)
        logging.info("saved {self}")
        return self

    def update(self):
        self.db.save(self)
        logging.info("updated {self}")
        return self

    @classmethod
    def all(cls):
        return cls.db.all()


def generate_validator(model: Saveable, create: bool = False):
    logging.warning("Validator not defined.")
    return []


CUSTOMER_NOTIFIED = "CUSTOMER_NOTIFIED"
BUSINESS_NOTIFIED = "BUSINESS_NOTIFIED"


@dataclass
class TransactionBase:
    amount: Decimal
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
    card: str
    details: str


class Transaction(TransactionBase, Saveable):
    @classmethod
    def from_raiffeisenbank_msg_part(cls, part):
        doc = etree.HTML(part)
        trs = doc.xpath("//tbody//tr")
        parsed_table = {
            "\n".join(tr.xpath("td[position()=1]/p/text()"))
            .strip(): "\n".join(tr.xpath("td[position()=2]/p/text()"))
            .strip()
            for tr in trs
        }

        amount_raw, currency = parsed_table["Částka v měně účtu"].split(" ")
        amount = Decimal(amount_raw.replace(".", "").replace(",", "."))

        z_uctu = parsed_table.get("Z účtu", "")
        na_ucet = parsed_table.get("Na účet", "")

        account_src, _, account_src_name = z_uctu.partition("\n")
        account_dst, _, account_dst_name = na_ucet.partition("\n")

        logging.info(parsed_table)
        card = parsed_table.get("Debetní karta", "")
        details = parsed_table.get("Detaily", "")

        return cls(
            amount=amount,
            currency=currency,
            category=parsed_table["Kategorie pohybu"],
            type=parsed_table["Typ pohybu"],
            account_dst=account_dst,
            account_dst_name=account_dst,
            account_src=account_src,
            account_src_name=account_src_name,
            message_for_reciever=parsed_table.get("Zpráva pro příjemce"),
            note=parsed_table.get("Zpráva pro mne"),
            variabilni_symbol=parsed_table.get("Variabilní symbol"),
            konstantni_symbol=parsed_table.get("Konstantní symbol"),
            specificky_symbol=parsed_table.get("Specifický symbol"),
            card=card,
            details=details,
        )


class Person:
    name: str
    surname: str
    email_address: str


class Business:
    name: str
    representative: Person


@dataclass
class VoucherBase:
    amount: Decimal
    issue_datetime: datetime
    transaction: Transaction | None = None
    payment_registered_datetime: datetime | None = None
    invalidation_datetime: datetime | None = None
    customer: Person | None = None
    business: Business | None = None
    signature: str | None = None


@dataclass
class Voucher(VoucherBase, Saveable, Database):
    db = VouchersDB()

    def message(self):
        message = f"{self.amount} {self.issue_datetime.isoformat()}"
        return message

    def sign(self):
        SECRET_KEY = b"pseudorandomly generated server secret key"
        AUTH_SIZE = 16

        h = blake2b(digest_size=AUTH_SIZE, key=SECRET_KEY)
        message = self.message()
        h.update(bytes(message, ENCODING))
        return message, h.hexdigest()

    def verify(self):
        signature = self.signature
        good_sig = self.sign()
        return compare_digest(good_sig, signature)
