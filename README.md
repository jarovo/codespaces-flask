# GitHub Codespaces ♥️ Flask

Welcome to your shiny new Codespace running Flask! We've got everything fired up and running for you to explore Flask.

You've got a blank canvas to work on from a git perspective as well. There's a single initial commit with the what you're seeing right now - where you go from here is up to you!

Everything you do here is contained within this one codespace. There is no repository on GitHub yet. If and when you’re ready you can click "Publish Branch" and we’ll create your repository and push up your project. If you were just exploring then and have no further need for this code then you can simply delete your codespace and it's gone forever.


## To run the paygate
```shell
podman build . -t jfkpay
podman run jfkpay
```

## To run the robot
```shell
podman run \
    -v credentials.json:/app/credentials.json \
    --entrypoint /bin/bash jfkpay jfk_orders
```

## To test in the container
do the same as to run the paygate. On the end make sure this is executed:
```
QR_ACCOUNT=123456 \
QR_VARIABILNI_SYMBOL=12345 \
QR_KONSTANTNI_SYMBOL=2222 \
QR_VOUCHER_PASSWORD=foobarbaz \
python -m jfkpay.app
```