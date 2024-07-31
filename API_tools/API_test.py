from SpiraAPI import SpiraBot
import time
from serial.tools import list_ports

def list_serial_ports():
    """List available serial ports."""
    ports = list_ports.comports()
    available_ports = []

    for port in ports:
        available_ports.append(port.device)
        print(f"{len(available_ports)}. {port.device} - {port.description}")

    return available_ports


print("Available USB ports:")
available_ports = list_serial_ports()

if not available_ports:
    print("No available ports found. Exiting.")
    exit()

# Get user input to choose port
port_selection = 0
while port_selection < 1 or port_selection > len(available_ports):
    try:
        port_selection = int(input("Choose a port (number): "))
    except ValueError:
        print("Please enter a valid number.")

selected_port = available_ports[port_selection - 1]
print(f"You selected: {selected_port}")

# Create an instance of SpiraBot and connect to the selected port
robot = SpiraBot(port=selected_port)  # Replace "/dev/ttyUSB0" with the actual port name

# Connect to port
while not robot.is_connected():
    print("connecting to spirabot...\n")
    if robot.connect():
        print("Success!")
    else:
        time.sleep(1)


def test1():
    increment = 1
    rpm = 15
    amp = 2
    zone_time_sek = 10

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
        time.sleep(zone_time_sek)
        rpm += increment


test1()