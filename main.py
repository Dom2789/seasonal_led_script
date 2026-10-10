import json, sys
import paho.mqtt.client as mqtt
import logger as lg, logging
from time import sleep
from datetime import datetime

r, g, b = map(int, sys.argv[1:4])
brightness = int(sys.argv[4]) if len(sys.argv) > 4 else 255 # if no brigthness is set, set to 255

if len(sys.argv) > 5:
    path_logfile = sys.argv[5]
else:
    path_logfile = ""

BROKER = "192.168.1.225"
PORT = 1883

STATE_TOPIC = "led/living/1/state"
COMMAND_TOPIC = "led/living/1/set"

OFF_STATE = "OFF"               # device offline / last will -> release the lock
TARGET = {"state": "ON", "color": {"r": r, "g": g, "b": b}, "brightness": brightness}

lg.setup_logging(path_logfile, "led_strip_living", debug=True)
log = logging.getLogger("led_strip_living")

_lock = False


def matches_target(s: dict) -> bool:
    color = {k: s.get("color", {}).get(k) for k in ("r", "g", "b")}
    return (
        s.get("state") == TARGET["state"]
        and color == TARGET["color"]
        and s.get("brightness") == TARGET["brightness"]
    )

def is_dark_season():
    today = datetime.now()
    spring_start = datetime(today.year, 3, 20)
    autumn_start = datetime(today.year, 9, 22)
    if (today > spring_start) and (today < autumn_start):
        return False
    else:
        return True


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        log.error("Connect failed: %s", reason_code)
        return
    log.info("Connected, subscribing to %s", STATE_TOPIC)
    client.subscribe(STATE_TOPIC, qos=1)


def on_message(client, userdata, msg):
    global _lock

    if msg.retain:
        # Old retained state delivered on (re)connect, not a fresh boot report
        log.debug("Ignoring retained state")
        return

    try:
        state = json.loads(msg.payload)
    except (json.JSONDecodeError, UnicodeDecodeError):
        log.warning("Non-JSON state payload: %r", msg.payload)
        return

    if state.get("state") == OFF_STATE:
        _lock = False
        log.debug("unlocked")
        return

    if _lock:
        log.debug("already locked")
        return

    if matches_target(state):
        log.info("state already matches target")
        return

    if not is_dark_season():
        log.info("Color not changed, because it is summer")
        _lock = True
        return

    sleep(1)
    client.publish(COMMAND_TOPIC, json.dumps(TARGET), qos=1, retain=False)
    _lock = True
    log.info("State %s -> sent target %s", state, TARGET)


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="led_strip_living")
    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=60)
    client.connect_async(BROKER, PORT, keepalive=60)
    client.loop_forever(retry_first_connection=True)


if __name__ == "__main__":
    log.info(TARGET)
    main()

