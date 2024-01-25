# -*- coding: utf-8 -*-
import os
import flask
from flask import Flask, render_template, make_response, request, session, url_for
import requests
import logging
from dataclasses import dataclass

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery


import qrcode, qrcode.image.svg
from decimal import Decimal
from jfkpay.views import GroupAPI, ItemAPI

from qrplatba import QRPlatbaGenerator
from datetime import datetime, timedelta
from jfkpay.gservices import SCOPES

from jfkpay.config import QRCodeConfig
from jfkpay import orders, model
from jfkpay.gservices import build_service

# This variable specifies the name of a file that contains the OAuth 2.0
# information for this application, including its client_id and client_secret.
CLIENT_SECRETS_FILE = "client_secret.json"


APP_NAME = "jfkpay"

app = flask.Flask(APP_NAME)
# Note: A secret key is included in the sample so that it works.
# If you use this code in your application, replace this with a truly secret
# key. See https://flask.palletsprojects.com/quickstart/#sessions.
# TODO Replace
app.secret_key = "REPLACE ME - this value is here as a placeholder."


@app.route("/")
def hello_world():
    return print_index_table()


@app.route("/payment_gateway")
def pay():
    return render_template("payment_gateway.html")


@app.get("/payment_complete")
def payment_complete():
    return render_template("payment_complete.html")


def register_api(app, model, name):
    item = ItemAPI.as_view(f"{name}-item", model)
    app.add_url_rule(f"/{name}/<string:uuid>", view_func=item)

    group = GroupAPI.as_view(f"{name}-group", model)
    app.add_url_rule(f"/{name}/", view_func=group)


register_api(app, model.Business, "business")
register_api(app, model.Person, "person")
register_api(app, model.Voucher, "voucher")
register_api(app, model.Transaction, "payment")


@app.route("/transactions")
def transactions():
    gmail = googleapiclient.discovery.build(
        "gmail", "v1", credentials=get_credentials()
    )

    found_messages = list(
        orders.filter_by_subject(
            orders.get_mails(gmail, "me"), orders.REIFFEISENBANK_TRANACTION_SUBJECT
        )
    )
    app.logger.debug(f"Found messages {found_messages}")
    payment_info = []
    for msg in found_messages:
        name, subject, from_name = orders.read_mail(msg)
        parts = list(orders.read_parts(msg))
        for part in parts:
            try:
                payment_info.append(
                    model.Transaction.from_raiffeisenbank_msg_part(part)
                )
            except KeyError as error:
                app.logger.error(f"KeyError when parsing f{msg:} f{part:}")
    return payment_info


@app.route("/process_transactions")
def process_transactions():
    credentials = get_credentials()
    gmail = googleapiclient.discovery.build("gmail", "v1", credentials=credentials)
    try:
        found_messages = orders.load_transactions_infos(gmail)
        for msg in found_messages:
            payments = orders.process_payments(found_messages)
    except KeyError as error:
        app.logger.error(f"KeyError when parsing f{msg:} f{part:}")
    finally:
        return "DONE"


@app.route("/qr_code")
def qr_code():
    qr = qrcode.QRCode(image_factory=qrcode.image.svg.SvgPathImage)
    qr.add_data("Some data")
    qr.make(fit=True)

    img = qr.make_image(attrib={"class": "some-css-class"})

    return make_response(img.to_string(encoding="unicode")), {
        "content-type": "image/svg+xml"
    }


@app.route("/qr_payment_code")
def qr_payment_code():
    amount = Decimal(request.args.get("amount"))

    now = datetime.now()
    due = now + timedelta(minutes=QRCodeConfig.VALIDITY_MINUTES)
    voucher = model.Voucher(amount=amount, issue_datetime=now)
    voucher.save()
    message = " ".join(voucher.sign())
    url = url_for("voucher-item", uuid=voucher.uuid, _external=True)

    generator = QRPlatbaGenerator(
        QRCodeConfig.ACCOUNT,
        amount=amount,
        x_ks=QRCodeConfig.KONSTANTNI_SYMBOL,
        x_vs=voucher._id,
        x_id=voucher.uuid,
        x_url=url,
        message=message,
        due_date=due,
    )

    app.logger.info(f"generating qrcode {generator.get_text()}")

    # optional: custom box size and border
    img = generator.make_image(box_size=20, border=4)

    # optional: get SVG as a string.
    # Encoding has to be 'unicode', otherwise it will be encoded as bytes
    svg_data = img.to_string(encoding="unicode")
    return make_response(svg_data), {"content-type": "image/svg+xml"}


def get_credentials():
    if "credentials" not in flask.session:
        return flask.redirect("authorize")

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(**flask.session["credentials"])
    return credentials


@app.route("/authorize")
def authorize():
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES
    )

    # The URI created here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    # error.
    flow.redirect_uri = flask.url_for("oauth2callback", _external=True)

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type="offline",
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes="true",
    )

    # Store the state so the callback can verify the auth server response.
    flask.session["state"] = state

    return flask.redirect(authorization_url)


@app.route("/oauth2callback")
def oauth2callback():
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = flask.session["state"]

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state
    )
    flow.redirect_uri = flask.url_for("oauth2callback", _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    flask.session["credentials"] = credentials_to_dict(credentials)

    return flask.redirect(flask.url_for("test_api_request"))


@app.route("/revoke")
def revoke():
    if "credentials" not in flask.session:
        return (
            'You need to <a href="/authorize">authorize</a> before '
            + "testing the code to revoke credentials."
        )

    credentials = google.oauth2.credentials.Credentials(**flask.session["credentials"])

    revoke = requests.post(
        "https://oauth2.googleapis.com/revoke",
        params={"token": credentials.token},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )

    status_code = getattr(revoke, "status_code")
    if status_code == 200:
        return "Credentials successfully revoked." + print_index_table()
    else:
        return "An error occurred." + print_index_table()


@app.route("/clear")
def clear_credentials():
    if "credentials" in flask.session:
        del flask.session["credentials"]
    return "Credentials have been cleared.<br><br>" + print_index_table()


def credentials_to_dict(credentials):
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }


def print_index_table():
    return render_template("index.html", title=APP_NAME)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # When running locally, disable OAuthlib's HTTPs verification.
    # ACTION ITEM for developers:
    #     When running in production *do not* leave this option enabled.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    # Specify a hostname and port that are set as a valid redirect URI
    # for your API project in the Google API Console.
    app.run("0.0.0.0", 8081, debug=True)
