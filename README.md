# ruuvitags-mqtt


## Install instructions

Replace `markku:markku` with your current unprivileged username and group:

    sudo mkdir /opt/ruuvitags-mqtt
    sudo chown markku:markku /opt/ruuvitags-mqtt
    cd /opt/ruuvitags-mqtt
    git clone https://github.com/markkuleinio/ruuvitags-mqtt.git .
    python3 -m venv venv
    venv/bin/pip install -U pip wheel
    venv/bin/pip install paho-mqtt ruuvitag-sensor
    sudo adduser --system ruuvitag
    sudo cp ruuvitags-mqtt.service /etc/systemd/system
    sudo systemctl daemon-reload
    sudo systemctl enable ruuvitags-mqtt.service --now


