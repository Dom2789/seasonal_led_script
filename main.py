import json, sys
import logger as lg, logging
import time

import paho.mqtt.client as mqtt

BROKER = "192.168.1.225"
PORT = 1883
STATE_TOPIC = "home/led_office_1/state"
COMMAND_TOPIC = "home/led_office_1/set"

TARGET = {"state": "ON", "color": {"r": 255, "g": 0, "b": 80}, "brightness": 200}
COOLDOWN_S = 5.0                # loop guard: max one command per window

lg.setup_logging("", "seasonal_color")
log = logging.getLogger("led-listener")
_last_sent = 0.0

r, g, b = map(int, sys.argv[1:4])
brightness = int(sys.argv[4]) if len(sys.argv) > 4 else 255

def matches_target(s: dict) -> bool:
    color = {k: s.get("color", {}).get(k) for k in ("r", "g", "b")}
    return (
        s.get("state") == TARGET["state"]
        and color == TARGET["color"]
        and s.get("brightness") == TARGET["brightness"]
    )


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        log.error("Connect failed: %s", reason_code)
        return
    log.info("Connected, subscribing to %s", STATE_TOPIC)
    client.subscribe(STATE_TOPIC, qos=1)


def on_message(client, userdata, msg):
    global _last_sent
    if msg.retain:
        # Old retained state delivered on (re)connect, not a fresh boot report
        log.debug("Ignoring retained state")
        return
    try:
        state = json.loads(msg.payload)
    except (json.JSONDecodeError, UnicodeDecodeError):
        log.warning("Non-JSON state payload: %r", msg.payload)
        return

    if matches_target(state):
        log.debug("State already matches target")
        return

    now = time.monotonic()
    if now - _last_sent < COOLDOWN_S:
        log.warning("State still differs after command, cooldown active: %s", state)
        return

    client.publish(COMMAND_TOPIC, json.dumps(TARGET), qos=1, retain=False)
    _last_sent = now
    log.info("State %s -> sent target %s", state, TARGET)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="led-listener")
    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=60)
    client.connect_async(BROKER, PORT, keepalive=60)
    client.loop_forever(retry_first_connection=True)


if __name__ == "__main__":
    log.info("hello log")
    log.info(f"{r} {g} {b} {brightness}")
    #main()

