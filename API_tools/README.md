# SpiraBot Python API

A Python API designed to interface and control the SpiraBot using serial communication.

## Installation

1. Ensure you have Python3 installed.
2. Install the required libraries:

```bash
pip3 install -r requirements.txt
```

## Usage

First, ensure you've imported the necessary libraries and the `SpiraBot` class:
```python
from spira_api import SpiraBot
```


### Initialize
Create a Spirabot instance by specifying the port (and optionally, the baudrate):
```
spirabot = SpiraBot(port="/dev/ttyUSB0", baudrate=115200)
````

### Connect/Disconnect
Connect to the SpiraBot:
````
spirabot.connect()
````

Check if connected:
```
status = spirabot.is_connected()
```
Disconnect from the SpiraBot:
````
spirabot.disconnect()
`````
## Control Commands
To change rpm or amplitude while a movement is running, the robot has to be fully stoped using ``spirabot.stop()``, and then startd again using ``spirabot.start_sine(amp, rpm)``. See the function ``spirabot.wait_for_idle()`` for applications where new sine settings should run directly after the last one finishes.

Start Sine movement (amplitude in millimeters):
````
spirabot.start_sine(amp=2, rpm=12)
````
Stop the movement:
````
spirabot.stop()
````

Start latest movement:
````
spirabot.start()
````

## Advanced Control Commands

In this example from API_test.py, the ``spirabot.wait_for_idle()``function is used to make a ramp ump sequence with seamless increments in rpm. The robot always finishes a full "breath"/cycle. After a stop-command, the wait-for-idle function could be used to pause the program until the robot returns to idle. Timeout defaults to 5 sek. This is demonstrated in this example:
 ````
increment = 1
rpm = 15
amp = 2
intervall_time_sec = 10

while True:

    robot.stop()
        
    if robot.wait_for_idle(timeout=5):
        print("robot is idle")

    else:
        print("robot did not reach idle before timeout")
        
    if rpm > 50:
        amp = 1
        
    else:
        amp = 2

    if rpm > 100:
        increment = -1

    elif rpm < 10:
        increment = 1

    robot.start_sine(amp, rpm)
    time.sleep(intervall_time_sec)
    rpm += increment
````
Absolute Positioning:
Set the start position for the movement in millimeters in the range [1, 20].
````
spirabot.abs_pos(pos=10)
````

Set microstep. Only valid settings are 1, 2 or 8.
````
spirabot.set_micro_step(m_step=4)
````

Set Amnesia. Amnesia set to False means that the robot starts at the same settings it had when it was powered off.
`````
spirabot.set_amnesia(0)

`````

# SpiraAPI_example.py

The simplest and fastes way to interact with the spirabot is to use the command-line-tool by running SpiraAPI_example.py