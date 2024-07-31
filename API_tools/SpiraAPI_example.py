from SpiraAPI import SpiraBot
import time
from serial.tools import list_ports
import serial
import random
from datetime import datetime

# device_identifier = "CP2104 USB to UART Bridge Controller"
device_identifier = "USB JTAG/serial debug unit"

def list_device_serial_number():
    while True:
        ports = serial.tools.list_ports.comports()
        port_index = 1
        available_ports = []
        for port, desc, hwid in sorted(ports):
            # Adjust the identification condition as needed
            if device_identifier in desc:  
                # print(f"Found device on {port}")
                available_ports.append((port, desc))
                with serial.Serial(port, 115200, timeout=5) as ser:
                    line = ser.readline().decode('utf-8').strip()
                    print(f"{port_index}. Spirabot {line}")
                    break
        if len(available_ports) > 0:
            break      

    return available_ports


def list_serial_ports():
    """List available serial ports."""
    ports = list_ports.comports()
    print(ports)
    available_ports = []

    for port in ports:
        available_ports.append(port.device)
        print(f"{len(available_ports)}. {port.device} - {port.description}")

    return available_ports


def progress_bar(total_time):
    for i in range(total_time + 1):
        progress = (i / total_time) * 100
        if progress == 100:
            print(f"                                                                                                                ",end='\r')
        else:
            print(f"Progress: [{'=' * int(progress // 2)}{' ' * (50 - int(progress // 2))}] {total_time-i}s / {int(progress)}%", end='\r')
            #print(f"Progress: [{'=' * i}{' ' * (total_time - i)}] {total_time-i}s / {int(progress)}%", end='\r')
        time.sleep(1)


def radar_test(spirabot):
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"radar_test_{current_time}.txt"
    with open(filename, 'a') as log_file:
        # Write to log file
        print(f"timestamp waveform rpm amplitude[mm] origo[mm] ", file=log_file)

    # log_message = "init"
    # spirabot.init()
    # log_to_console_and_file(message=log_message, file_name=filename)
    step_duration = 60
    pause_duration = 20
    # while True:
    #    current_state = spirabot.status("current_state")
    #    if current_state == "1":
    #        break
    #    else:
    #        #print("Waiting for robot. Current state: ", current_state, "\n")
    #        log_to_console_and_file("Waiting for robot to finish current breath. Current state: " + str(current_state), filename)
    #        time.sleep(1)


    for origo in [1, 5, 10, 15, 20]:
        spirabot.abs_pos(origo)
        log_to_console_and_file(message=f"origo {origo}", file_name=filename)
        progress_bar(10)

        for rpm in range(5, 29):
    
            for amp in [0.5, 1, 1.5, 2, 2.5, 3]:
                while True:
                    current_state = spirabot.status("current_state")
                    if current_state == "1":
                        break
                    else:
                        #print("Waiting for robot. Current state: ", current_state, "\n")
                        log_to_console_and_file("Waiting for robot to finish current breath. Current state: " + str(current_state), filename)
                        time.sleep(1)
                spirabot.start_sine(amp, rpm)
                log_to_console_and_file(message=f"Starting sine with rpm: {rpm}, amp: {amp} and origo {origo} for {step_duration} seconds.", file_name=filename, rpm=rpm, amp=amp, origo=origo)
                progress_bar(step_duration)
                log_to_console_and_file("Pausing for " + str(pause_duration) + " seconds.", file_name=filename, rpm=0, amp=0, origo=0)
                robot.stop()
                progress_bar(pause_duration)
                




def log_to_console_and_file(message, file_name, rpm=-1, amp=-1, origo=-1):
    # Get the current timestamp
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    seconds_since_epoch = time.time()
    # Print to console
    print(current_time + " : " + message)
    # Open the file with the generated filename in append mode to log the message
    with open(file_name, 'a') as log_file:
        # Write to log file
        if (rpm < 0) or (amp < 0) or (origo < 0):
            print(f"{seconds_since_epoch} {message}", file=log_file)
        else:
            print(f"{seconds_since_epoch} sine {rpm} {amp} {origo}", file=log_file)


def random_sine(spirabot):
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"log_{current_time}.txt"
    with open(filename, 'a') as log_file:
        # Write to log file
        print(f"timestamp waveform rpm amplitude[mm] origo[mm] ", file=log_file)

    pause = False
    while True:
        duration_sek = random.randint(30, 120)
        if pause:
            while True:
                current_state = spirabot.status("current_state")
                if current_state == "1":
                    break
                else:
                    #print("Waiting for robot. Current state: ", current_state, "\n")
                    log_to_console_and_file("Waiting for robot to finish current breath. Current state: " + str(current_state), filename)
                    time.sleep(1)
            duration_sek = 120
            #print("Pausing for ", duration_sek, " seconds.")
            log_to_console_and_file("Pausing for " + str(duration_sek) + " seconds.", file_name=filename, rpm=0, amp=0, origo=0)
            robot.stop()
            progress_bar(duration_sek)
            pause = False
        else:
            while True:
                current_state = spirabot.status("current_state")
                if current_state == "1":
                    break
                else:
                    #print("Waiting for robot. Current state: ", current_state, "\n")
                    log_to_console_and_file("Waiting for robot to finish current breath. Current state: " + str(current_state), filename, -1, -1, -1)
                    time.sleep(1)
            rpm = random.randint(5, 40)
            amp = random.randint(10, 20)/10
            #print("Starting sine with rpm: ", rpm, " and amp: ", amp, " for ", duration_sek, " seconds.")
            log_to_console_and_file("Starting sine with rpm: " + str(rpm) + " and amp: " + str(amp) + " for " + str(duration_sek) + " seconds.", filename, rpm, amp, 0)
            spirabot.start_sine(amp, rpm)
            progress_bar(duration_sek)
            spirabot.stop()
            pause = True


def test1():
    increment = 1
    rpm = 15
    amp = 2
    zone_time_sek = 10

    while True:

        robot.stop()
        
        if robot.wait_for_idle(timeout=8):
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
        print(f"Starting sine: amp -> {amp}, rpm -> {rpm}")
        time.sleep(zone_time_sek)
        rpm += increment

if __name__ == '__main__':

    print("Available USB ports:")
    available_ports = list_serial_ports()
    # available_ports = list_device_serial_number()

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


    robot_serial_number = robot.get_serial_number()
    # robot_serial_number = "spirabot"
    print("Connected to Spirabot with serial number: ", robot_serial_number)

    print("#" * 50)
    print("########### SPIRABOT COMMAND LINE TOOL ##########")
    print("Use these commands to control the robot:")
    print("stop - stop the robot")
    print("sine <rpm> <amp> - start a sine movement with the given rpm and amp")
    print("sine random - start a random sine movement")
    print("status - get the status of the robot")
    print("status <variable> - get the value of a specific variable")
    print("microstep <step> - set the microstep value")
    print("abs_pos <pos> - move to the given absolute position")
    print("rel_pos <pos> - move the given relative position")
    print("slot <speed> - run to the slot with the given speed")
    print("test <number> - (1 = ramp up test)")
    print("amnesia <value> - set amnesia mode. Amnesia = 0 starts last pattern after reboot")
    print("exit - exit the program")

    while True:
        command_input = input(robot_serial_number + ": ")
        command_parts = command_input.split() # Split input by spaces

        command = command_parts[0]

        if command == "stop":
            robot.stop()

        elif command == "set_serial_number":
            if len(command_parts) == 2:
                robot.set_serial_number(command_parts[1])
            else:
                input_serial_number = input("Serial number: ")
                robot.set_serial_number(input_serial_number)
            robot_serial_number = robot.get_serial_number()

        elif command == "start":
            robot.start()

        elif command == "init":
            robot.init()

        elif command == "fw":
            if len(command_parts) == 2:
                if command_parts[1] == "flash":
                    robot.firmware_flash()
                elif command_parts[1] == "version":
                    print(robot.status("fw_hash"))
                else:
                    print("Did not recognize command.")
            else:
                print("Did not recognize command.")

        elif command == "test":
            if len(command_parts) == 2:
                if command_parts[1] == "1":
                    test1()
                else:
                    print("Did not recognize command.")
            else:
                radar_test(spirabot=robot)

        elif command == "amnesia":
            variable = command_parts[1]
            if variable == "1":
                robot.set_amnesia(value=1)
            
            elif variable == "0":
                robot.set_amnesia(value=0)

            else:
                print("Error: Invalid value for amnesia. Must be 0 or 1.")

        elif command == "curve_type":
            variable = command_parts[1]
            if variable == "1":
                print("Setting curve_type to sine (1)")
                robot.set_curve_type(1)
            
            elif variable == "2":
                print("Setting curve_type to double sine (2)")
                robot.set_curve_type(2)

            else:
                print("Error: Invalid value for curve_type. Must be 0 or 1.")

        elif command == "double_sine":
            if len(command_parts) == 3: # If parameters are provided
                rpm = command_parts[1]
                amp = command_parts[2]
                robot.start_pattern(amp, rpm, pattern=2)
            
            else:
                rpm = input("RPM: ")
                amp = input("amp: ")
                robot.start_pattern(amp, rpm, pattern=2)

        elif command == "sine":
            if len(command_parts) == 3: # If parameters are provided
                rpm = float(command_parts[1])
                amp = float(command_parts[2])
                #robot.start_sine(amp, rpm)
                robot.start_pattern(amp, rpm, pattern=1)

            elif len(command_parts) == 2: # If only rpm is provided
                print(command_parts)
                if command_parts[1] == "random":
                    random_sine(robot)
                else:
                    print("Did not recognize command.")
            
            else:
                rpm = float(input("RPM: "))
                amp = float(input("amp: "))
                #robot.start_sine(amp, rpm)
                robot.start_pattern(amp, rpm, pattern=1)
                
        elif command == "status":
            if len(command_parts) == 2: # If variable is provided
                variable = command_parts[1]
                try:
                    print(robot.status(variable=variable))
                except:
                    pass
            else:
                status = ""
                status_variables = ["serial_number", "fw_hash", "current_pos", "current_state", "amp", "rpm", "micro_step", "origo", "curve_mode", "amnesia"]
                print("Variables: ", status_variables)
                while status != "exit":
                    status = input("Variable: ")
                    if status in status_variables:
                        try:
                            print(robot.status(variable=status))
                        except:
                            pass
                    else:
                        print("Please write a valid attribute.")

        elif command == "microstep":
            if len(command_parts) == 2: # If step is provided
                micro_step = command_parts[1]
                robot.set_micro_step(micro_step)
            else:
                micro_step = input("micro step: ")
                robot.set_micro_step(micro_step)

        elif command == "abs_pos":
            if len(command_parts) == 2: # If position is provided
                pos = command_parts[1]
                try:
                    pos = int(pos)
                    robot.abs_pos(pos)
                except:
                    pass
            else:
                pos = 0
                while pos != "exit":
                    pos = input("abs_pos (mm): ")
                    try:
                        pos = int(pos)
                        robot.abs_pos(pos)
                    except:
                        pass

        elif command == "rel_pos":
            if len(command_parts) == 2:
                pos = command_parts[1]
                try:
                    pos = int(pos)
                    robot.rel_pos(pos)
                except:
                    pass
            else:
                pos = 0
                while pos != "exit":
                    pos = input("rel_pos (mm): ")
                    try:
                        pos = int(pos)
                        robot.rel_pos(pos)
                    except:
                        pass

        elif command == "slot":
            if len(command_parts) == 2: # If position is provided
                speed = command_parts[1]
                try:
                    speed = int(speed)
                    robot.run_to_slot(-1, speed)
                except:
                    pass
            else:
                speed = 0

                speed = input("Speed: ")
                try:
                    speed = int(speed)
                    robot.run_to_slot(-1, speed)
                except:
                    pass

        

