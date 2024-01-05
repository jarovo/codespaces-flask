from flask import Flask, render_template, make_response
import qrcode, qrcode.image.svg

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