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
    # key: (name, unit, device_class, entity_category, icon, value_template, suggested_display_precision)
    "temperature": ("Temperature", "°C", "temperature", None, None, "value_json.temperature", None),
    "humidity": ("Humidity", "%", "humidity", None, None, "value_json.humidity", None),
    "pressure": ("Pressure", "hPa", "atmospheric_pressure", None, "mdi:gauge", "value_json.pressure", None),
    "battery": ("Battery Voltage", "V", "voltage", None, "mdi:current-dc", "(value_json.battery | float / 1000) | round(3)", 3),
    "rssi": ("RSSI", "dBm", "signal_strength", "diagnostic", None, "value_json.rssi", None),
}
UPDATE_INTERVAL = 60

discovered_sensors = set()
last_updated = {}

logger = logging.getLogger()


def publish_discovery(sensor_id: str, mqtt_client: mqtt.Client) -> None:
    device_id = f"ruuvi_{sensor_id}"
    components = {}
    for key, (name, unit, device_class, entity_category, icon, value_template, precision) in SENSORS.items():
        item = {
            "platform": "sensor",
            "name": name,
            "unique_id": f"{device_id}_{key}",
            "device_class": device_class,
            "state_class": "measurement",
            "unit_of_measurement": unit,
            "entity_category": entity_category,
            "value_template": "{{ " + value_template + " }}",
            "suggested_display_precision": precision,
            "icon": icon,
        }
        # Save only fields with non-None values
        components[key] = {k: v for k, v in item.items() if v is not None}
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

