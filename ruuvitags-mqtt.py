import asyncio
import configparser
import json
import logging
from pathlib import Path
import time

import paho.mqtt.client as mqtt
from ruuvitag_sensor.ruuvi import RuuviTagSensor


CONFIG_FILE = Path(__file__).parent / "ruuvitags-mqtt.cfg"
SENSORS = {
    "temperature": ("Temperature", "°C", "temperature"),
    "humidity": ("Humidity", "%", "humidity"),
    "pressure": ("Pressure", "hPa", "atmospheric_pressure"),
    "battery": ("Battery Voltage", "mV", "voltage"),
    "rssi": ("RSSI", "dBm", "signal_strength"),
}
DIAGNOSTIC_SENSORS = (
    # These will set entity_category to diagnostic
    "rssi",
)
UPDATE_INTERVAL = 60

discovered_sensors = set()
last_updated = {}

logger = logging.getLogger()


def publish_discovery(sensor_id: str, mqtt_client: mqtt.Client) -> None:
    device_id = f"ruuvi_{sensor_id}"
    components = {}
    for key, (name, unit, device_class) in SENSORS.items():
        components[key] = {
            "platform": "sensor",
            "name": name,
            "unique_id": f"{device_id}_{key}",
            "device_class": device_class,
            "state_class": "measurement",
            "unit_of_measurement": unit,
            "value_template": "{{ value_json." + key + " }}",
        }
        if key in DIAGNOSTIC_SENSORS:
            components[key]["entity_category"] = "diagnostic"
    config = {
        "device": {
            "identifiers": [device_id],
            "name": f"RuuviTag {sensor_id}",
            "manufacturer": "Ruuvi",
            "model": "RuuviTag",
        },
        "origin": {
            "name": "ruuvitags-mqtt",
            "sw_version": "0.1",
        },
        "state_topic": f"ruuvi/{sensor_id}/state",
        "components": components,
    }
    topic = f"homeassistant/device/{device_id}/config"
    logger.info(f"Publishing: {topic}")
    mqtt_client.publish(
        topic,
        json.dumps(config),
        qos=1,
        retain=True,
    )


def publish_data(sensor_id: str, data: dict, mqtt_client: mqtt.Client) -> None:
    topic = f"ruuvi/{sensor_id}/state"
    logger.debug(f"Publishing: {topic}")
    mqtt_client.publish(
        topic,
        json.dumps(data),
        qos=1,
        retain=True,
    )


async def main(mqtt_client: mqtt.Client):
    async for found_data in RuuviTagSensor.get_data_async():
        mac, data = found_data
        sensor_id = mac.lower().replace(":", "")
        if sensor_id not in discovered_sensors:
            publish_discovery(sensor_id, mqtt_client)
            discovered_sensors.add(sensor_id)
            last_updated[sensor_id] = -9999.0
        # Only publish data for a RuuviTag after UPDATE_INTERVAL seconds
        # have elapsed since last publish
        curr_time = time.monotonic()
        if curr_time - last_updated[sensor_id] > UPDATE_INTERVAL:
            last_updated[sensor_id] = curr_time
            publish_data(sensor_id, data, mqtt_client)


if __name__ == "__main__":
    logger.setLevel(logging.INFO)
    logging.getLogger("ruuvitag_sensor").setLevel(logging.ERROR)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    host = config["mqtt"]["host"]
    port = config["mqtt"].getint("port")
    mqtt_client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="ruuvitags-mqtt",
    )
    mqtt_client.username_pw_set(config["mqtt"]["user"], config["mqtt"]["password"])
    mqtt_client.connect_async(host, port)
    mqtt_client.loop_start()
    logger.info("Connected to %s:%d", host, port)
    try:
        asyncio.run(main(mqtt_client))
    except KeyboardInterrupt:
        print()

