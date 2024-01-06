from flask import Flask, render_template, make_response
import qrcode, qrcode.image.svg

from qrplatba import QRPlatbaGenerator
from datetime import datetime, timedelta


app = Flask(__name__)

@app.route("/")
def hello_world():
    return render_template("index.html", title="Hello")


@app.route("/payment")
def pay():
    return render_template("payment.html")


@app.route("/qr_code")
def qr_code():
    qr = qrcode.QRCode(image_factory=qrcode.image.svg.SvgPathImage)
    qr.add_data('Some data')
    qr.make(fit=True)

    img = qr.make_image(attrib={'class': 'some-css-class'})

    return make_response(img.to_string(encoding='unicode')), {'content-type': 'image/svg+xml'}


@app.route("/qr_payment_code")
def qr_payment_code():
    due = datetime.now() + timedelta(days=14)
    generator = QRPlatbaGenerator('123456789/0123', 400.56, x_vs=2034456, message='text', due_date=due)
    img = generator.make_image()

    # optional: custom box size and border
    img = generator.make_image(box_size=20, border=4)

    # optional: get SVG as a string.
    # Encoding has to be 'unicode', otherwise it will be encoded as bytes
    svg_data = img.to_string(encoding='unicode')
    return make_response(svg_data), {'content-type': 'image/svg+xml'}