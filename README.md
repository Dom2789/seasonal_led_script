# change_color_seasonal

Keeps an MQTT LED strip at a fixed color during the dark half of the year
(22.09. – 20.03.).

The script subscribes to the strip's state topic and waits. As soon as the strip
reports that it was switched on with anything other than the target color, the
target is published once to the command topic. After that it stays quiet until
the strip reports `OFF` again — so manual color changes made while the light is
on are not overridden. Outside the dark season nothing is sent at all.

Retained state messages (delivered on reconnect) are ignored, so a restart of
the script does not trigger a command on its own.

## Usage

```
uv run main.py <r> <g> <b> [brightness] [logfile_path]
```

| Argument       | Default | Description                                  |
| -------------- | ------- | -------------------------------------------- |
| `r` `g` `b`    | —       | target color, 0–255 each (required)          |
| `brightness`   | `255`   | target brightness, 0–255                     |
| `logfile_path` | `""`    | directory for the log file, with trailing `/` |

Example:

```
uv run main.py 240 3 252 100
```

The log is written to `led_strip_living.log` in `logfile_path` (current
directory if omitted).

## Configuration

Broker, port and topics are constants at the top of `main.py`:

```python
BROKER = "192.168.1.225"
PORT = 1883
STATE_TOPIC = "led/living/1/state"
COMMAND_TOPIC = "led/living/1/set"
```

## Run as a service

`led_strip_living.service` runs the script as a systemd unit, restarting it
automatically. Adjust the paths and color in `ExecStart`, then:

```
cp led_strip_living.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now led_strip_living
```