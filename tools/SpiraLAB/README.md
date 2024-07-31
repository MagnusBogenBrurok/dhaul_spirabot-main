markdown
Copy code
# SpiraBot Library

The SpiraBot library provides a Python interface to control a robot via UART communication. It allows you to send commands and data to the robot, making it easy to control various aspects of its behavior.

## Installation

To use the SpiraBot library, follow these steps:

1. Download the `spira_bot.py` file and place it in your project directory.
2. Make sure you have the `json` and `serial` libraries installed. If not, you can install them using `pip`:

```
pip install json
pip install pyserial
```

## Usage

### Creating a SpiraBot Instance

To get started, create an instance of the `SpiraBot` class by providing the serial port and baud rate as parameters:

```python
from spira_bot import SpiraBot

# Replace '/dev/ttyUSB0' with the correct serial port for your robot
spira_bot = SpiraBot(port='/dev/ttyUSB0', baudrate=115200)
```
### Connecting and Disconnecting
You can connect to the robot using the connect() method:

```python
connected = spira_bot.connect()
if connected:
    print("Connected to the robot.")
else:
    print("Failed to connect.")
```

To disconnect from the robot, use the disconnect() method:

```python
spira_bot.disconnect()
```
### Controlling the Robot
The SpiraBot library provides several methods to control the robot:

- start(loop_count=-1): Start the robot's operation with an optional loop count that defaults to -1 (infinite loop)
- stop(): Stop the robot's operation.
- set_flag(flag, value, send_data=False): Set a specific flag to a value. Use send_data=True to immediately send the updated data to the robot.
- set_loop_count(loop_count, send_data=False): Set the loop count for the robot's operation.
- set_origo(origo, send_data=False): Set the robot's origin position.
- set_micro_steps(micro_step, send_data=False): Set the micro-stepping value for the robot.
- set_freq(freq, send_data=False): Set the frequency of the robot's operation.

### Uploading Curve Data
You can upload a custom curve to the robot using the upload_curve(curve, send_data=False) method. The curve parameter should be a list of integer values representing the curve data.

Alternatively, you can upload curve data from a file using the upload_curve_from_file(filename) method. The file should be in CSV format, where each line represents a data point of the curve.

### Sending Data
To send all the data to the robot, use the send_all_data() method:

```python
spira_bot.send_all_data()
```
You can also send specific data attributes using the send_data(data_attributes) method:

```python
spira_bot.send_data(["start", "stop", "loop_count"])
```
### Getting Data
To retrieve the current data stored in the SpiraBot instance, use the get_data() method:

```python
data = spira_bot.get_data()
print(data)
```
## Examples

```python
# Create a SpiraBot instance and connect to the robot
spira_bot = SpiraBot(port='/dev/ttyUSB0', baudrate=115200)
connected = spira_bot.connect()

# Set the loop count and start the robot's operation
spira_bot.set_loop_count(loop_count=3)
spira_bot.start()

# Upload a curve from a file and send the data to the robot
spira_bot.upload_curve_from_file('curve_data.csv')
spira_bot.send_all_data()

# Stop the robot's operation and disconnect
spira_bot.stop()
spira_bot.disconnect()
```

## Notes

The library is designed to work with a specific robot using UART communication. Ensure that you have the correct serial port and baud rate configured.
Make sure to handle exceptions appropriately when using the library, such as ConnectionError when the robot is not connected.
Refer to the documentation of your robot to understand the meanings of different flags and data attributes used by the SpiraBot library.

Feel free to copy and paste this content into your README.md file for the SpiraBot library.



