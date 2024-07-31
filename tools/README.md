# SPIRABOT UART Controller

*This tool is still under development.

## 🧐 About

This Python script allows you to control the SPIRABOT device over UART using a serial connection. It provides a command-line interface to send commands and control various parameters of the device.


## ⛏️ Prerequisites

- Python == 3.11.2
- PySerial == 3.5

## 🏁 Usage

1. Connect the SPIRABOT device to your computer via a USB serial connection.

2. Run the Python script `UART_controller.py` 
3. The script will detect available serial ports and prompt you to select the desired port. Follow the instructions displayed on the terminal to select the port.

4. Once connected, you will see the SPIRABOT UART Controller command prompt `(SPIRABOT)<port_name>: ` where `<port_name>` represents the selected serial port.

5. Available commands:
- `start`: Start respiration on the SPIRABOT device.
- `stop`: Stop respiration on the SPIRABOT device.
- `amp`: Set the amplitude of the respiration on the SPIRABOT device.. Enter the desired amplitude when prompted. The amplitude is given in milimeters (int).
- `speed`: Set the speed of the respiration on the SPIRABOT device. Enter the desired speed when prompted. The speed is given in Hz (steps/second). The step length is 0.01mm, so a speed of 100 equals 1mm/second. This is the start speed of the movement and some acceleration is added, but this can not be controlled from this script.
- `help`: Display the list of available commands.

6. Enter the desired command at the prompt and follow any additional prompts if required.

7. The script will convert the command and parameters into a JSON string and send it over the UART connection to the SPIRABOT device.

8. The script will continue running until interrupted. To exit, press `Ctrl+C` in the terminal.

## 💻 Example

Here's an example session using the SPIRABOT UART Controller:

```bash
################### DETECTED PORTS ###################
0 /dev/cu.Bluetooth-Incoming-Port
1 /dev/cu.Svartdiamant
2 /dev/cu.usbserial-1110
3 /dev/cu.wlan-debug
######################################################
Select port (nr): 2
Trying to connect to  /dev/cu.usbserial-1110
Connection succeeded!
Connected to  /dev/cu.usbserial-1110

 

################################################################
################### SPIRABOT UART CONTROLLER ###################
################################################################
Command list:  ['start', 'stop', 'amp', 'speed', 'help']
(SPIRABOT)/dev/ttyUSB0: amp
-> 3
(SPIRABOT)/dev/ttyUSB0: speed
-> 50
(SPIRABOT)/dev/ttyUSB0: start
(SPIRABOT)/dev/cu.usbserial-1110: help
Command list:  ['start', 'stop', 'amp', 'speed', 'help']
(SPIRABOT)/dev/ttyUSB0: stop
```


## ✍️ Authros
- Magnus Bogen [@MagnusBogen](https://github.com/MagnusBogen)