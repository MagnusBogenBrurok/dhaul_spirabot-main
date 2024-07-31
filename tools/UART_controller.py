import serial.tools.list_ports
import time
import json

# Load the configuration from the file
with open("config.json", "r") as f:
    config = json.load(f)

# Access the data and command list
data = config["data"]
command_list = ["init", "start", "start_sine", "stop", "amp", "speed", "calibration", "help"]
print_sent_data = True

connected = False
port_index = 0
port_list = []

def connect_port():
    ports = serial.tools.list_ports.comports()
    connected = False
    port_index = 0
    port_list = []
    print("\n", "\n")
    print("################### DETECTED PORTS ###################")
    for port, desc, hwid in sorted(ports):
        # print("{}: {} [{}]".format(port, desc, hwid))
        port_list.append(port)
        print(port_index, port)
        port_index += 1
    print("######################################################")

    while not connected:
        selected_port = int(input("Select port (nr): "))
        print("Trying to connect to ", port_list[selected_port])
        time.sleep(1)
        try:
            ser = serial.Serial(port_list[selected_port], 115200)  # open serial port
            print("Connection succeeded!")
            time.sleep(1)
            print("Connected to ", ser.name)  
            connected = True   
            break;    # check which port was really used

        except:
            print("could not connect..")
            ser
            time.sleep(5)

    # Wait for the ESP32 to initialize
    time.sleep(1)
    return ser


def send_message(message, serial_port):
    # message = b'MAC: Hello, ESP32!'
    msg = message.encode('ascii')
    serial_port.write(msg)


def run_main():

    ser = connect_port()
    print("\n", "\n")
    print("################################################################")
    print("################### SPIRABOT UART CONTROLLER ###################")
    print("################################################################")

    print("Command list: ", command_list)

    while True:
        send_data = config["data"]
        send_data["calibration"] = int(0)
        try:
            command = input("(SPIRABOT)" + ser.name + ": ")
            send_data["init"] = int(0)
            if command not in command_list:
                print("Invalid command")
            elif command == "init":
                send_data["init"] = int(1)
            elif command == "stop":
                send_data["stop"] = int(1)
            elif command == "calibration":
                send_data["calibration"] = int(1)
            elif command == "start":
                send_data["start"] = int(1)
            elif command == "start_sine":
                send_data["start_sine"] = int(1)
            elif command == "amp":
                send_data["amplitude"] = int(input("-> "))
            elif command == "speed":
                send_data["speed"] = int(input("-> "))
            elif command == "help":
                print("Command list: ", command_list)

            json_str = json.dumps(send_data) + '\n'  # Append newline character

            # Send the JSON string over UART
            ser.write(json_str.encode())

            #Print JSON
            if print_sent_data:
                print(json_str)

        except:
            ser = connect_port()

        

    # Close the serial connection
    ser.close()


run_main()