# ruuvitags-mqtt

The app receives the Bluetooth messages from RuuviTags with the built-in
Bluetooth adapter of Raspberry Pi and sends them to the MQTT broker as messages
that Home Assistant can use for device discovery and data values.

Tested with `paho-mqtt` 2.1.0 and `ruuvitag-sensor` 4.1.0.

## Install instructions

Replace `markku:markku` with your current unprivileged username and group:

    sudo mkdir /opt/ruuvitags-mqtt
    sudo chown markku:markku /opt/ruuvitags-mqtt
    cd /opt/ruuvitags-mqtt
    git clone https://github.com/markkuleinio/ruuvitags-mqtt.git .
    cp ruuvitags-mqtt.cfg.example ruuvitags-mqtt.cfg
    vi ruuvitags-mqtt.service   # or use some other editor
    python3 -m venv venv
    venv/bin/pip install -U pip wheel
    venv/bin/pip install paho-mqtt ruuvitag-sensor
    sudo adduser --system ruuvitag
    sudo cp ruuvitags-mqtt.service /etc/systemd/system
    sudo systemctl daemon-reload
    sudo systemctl enable ruuvitags-mqtt.service --now


