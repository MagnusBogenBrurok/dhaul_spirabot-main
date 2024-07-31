import serial
import json
import time
import os
# import esptool

class SpiraBot:
    def __init__(self, port, baudrate=115200):
        """
        Initialize the SpiraBot instance.

        Args:
        - port: Serial port for the robot connection.
        - baudrate: Baud rate for the serial communication. Default is 115200.
        """

        self.config = self._load_config()
        self.port = port
        self.baudrate = baudrate
        self._serial = None
        self._connected = False
        self._firmware_hash = ""
        self._serial_number = ""
        self._data_msg = self.config["default_settings"]
        self._read_error = self.config["read_error"]


    def set_curve_type(self, curve_type):
        """
        Set the curve type for the robot.

        Args:
        - curve_type: Curve type to set.
        """
        curve_type = int(curve_type)
        if curve_type not in [1, 2]:
            #raise ValueError("Curve type must be 1 or 2.")
            print("Curve type must be 1 or 2.")

        else:
            self._data_msg["curve_type"] = int(curve_type)
            self.send_data(["curve_type"])
            time.sleep(0.05)

    def firmware_flash(self):
        """
        !BETA!
        To flash new firmware look for a file called "fw_flash_mac.sh" or "fw_flash_win.bat" in the firmware folder.

        Flash firmware onto the ESP32 connected to the specified port.
        """
        current_directory = os.path.dirname(os.path.realpath(__file__))

        # Path to the bootloader binary
        bootloader_path = os.path.join(current_directory, 'firmware/bootloader.bin')  
        
        # Path to the partition table binary
        partitions_path = os.path.join(current_directory, 'firmware/partitions.bin') 

        # Path to the firmware binary
        firmware_path = os.path.join(current_directory, 'firmware/firmware.bin')

        command = [
            '--chip', 'esp32',
            '--port', self.port,
            '--baud', '115200',
            '--before', 'default_reset',
            '--after', 'hard_reset',
            'write_flash', '-z',
            '--flash_mode', 'dio',
            '--flash_freq', '40m',
            '--flash_size', 'detect',
            '0x1000', bootloader_path,
            '0x10000', firmware_path,
            '0x8000', partitions_path
            ]

        # Run the command
        print('Using command %s' % ' '.join(command))
        esptool.main(command)

    def get_serial_number(self):
        """
        !BETA!
        This function is not yet implemented in the firmware.

        Retrieve and set the serial number of the robot.
        """
        sn = self.status(variable="serial_number")
        if (sn["success"]):
            self._serial_number = sn["data_received"]
            return self._serial_number

    def serial_number(self):
        """
        !BETA!
        This function is not yet implemented in the firmware.

        Retrieve the serial number of the robot.

        Returns:
        - Serial number of the robot.
        """
        return self._serial_number

    def set_serial_number(self, serial_number):
        """
        !BETA!
        This function is not yet implemented in the firmware.

        Set the serial number of the robot.

        Args:
        - serial_number: Serial number to set.
        """
        if len(serial_number) != 14:
            raise ValueError("Serial number must be 12 characters long.")
        else:
            self._serial_number = serial_number
            self._data_msg["serial_number"] = serial_number
            self.send_data(["serial_number"])

    def _load_config(self, config_file="config.json"):
        """
        Load configuration settings from a JSON file.

        Returns:
        - Dictionary containing the loaded configuration.
        """
        with open(config_file, 'r') as file:
            return json.load(file)

    def init(self):
        """
        Initialize the robot.
        """
        self._data_msg["init"] = 1
        self.send_data(["init"])

    def start(self, loop_count=-1):
        """
        Start robot movement.

        Args:
        - loop_count: Number of iterations for movement. Default is -1 for infinite.
        """

        self._set_flag(flag="stop", value=0)
        self.send_data(["stop"])
        if self._read_error:
            self.read_error()

    def start_pattern(self, amp, rpm, pattern=2,loop_count=-1):
        """
        Start pattern movement.
        
        Args:
        - pattern_number: Pattern to use. Currently only one avauiable.
        - amp: Amplitude of movement in millimeters. Stroke lenmgth is 2*amp.
        - rpm: Respirations per minute.
        """
        # self.set_curve_type(int(pattern))

        self._data_msg["curve_type"] = int(pattern)
        self._data_msg["amp"] = float(amp)
        self._data_msg["rpm"] = float(rpm)
        self._data_msg["loop_count"] = loop_count
        self._data_msg["stop"] = 0
        self.send_data(["amp", "rpm", "loop_count", "stop", "curve_type"])
        if self._read_error:
            self.read_error()

    def start_sine(self, amp, rpm, loop_count=-1):
        """
        Start sinusoidal movement.

        Args:
        - amp: Amplitude of movement in millimeters. Stroke lenmgth is 2*amp.
        - rpm: Respirations per minute.
        - loop_count: Number of iterations. Default is -1 for infinite.
        """

        #print(f"Curve type: {self._data_msg['curve_type']}")

        self.set_curve_type(1)
        
        self._data_msg["amp"] = float(amp)
        self._data_msg["rpm"] = float(rpm)
        self._data_msg["loop_count"] = loop_count
        self._data_msg["stop"] = 0
        self.send_data(["amp", "rpm", "loop_count", "stop"])
        if self._read_error:
            self.read_error()

    def wait_for_idle(self, timeout=5, wait_time=0.1):
        """
        Wait for the robot to reach idle.

        Args:
        - timeout: Maximum time to wait for idle.
        - wait_time: Time interval between checks.
        """

        start_time = time.time()

        while True:
            elapsed_time = time.time() - start_time

            if elapsed_time > timeout:
                return False  # Timeout reached

            status_result = self.status(variable="current_state")

            if status_result["success"]:
                current_state = status_result["data_received"]
                if current_state == "1":
                    return True  # Robot is idle

                elif current_state == "3":
                    time.sleep(wait_time)  # Wait before checking again
                    continue  # Check status again

                else:
                    # Handle unexpected state or errors
                    return False

            else:
                # Handle status request failure
                return False

    def status(self, variable="fw_hash", time_out=2):
        """
        Retrieve status information from the robot.

        Args:
        - variable: Variable to retrieve status information for.
        - time_out: Timeout duration for status retrieval.

        Returns:
        - Dictionary with status retrieval result.
        """
        status_prefix = "***STATUS***"

        self._serial.flush()
        start_time = time.time()
        self._data_msg["status_request"] = variable
        self.send_data(["status_request"])
        time.sleep(0.1)

        received_data = None
        success = False
        error_message = None

        while True:
            raw_data = self._serial.readline()
            decoded_data = raw_data.decode().strip()  # Decode the bytes to a string and remove leading/trailing whitespace
            elapsed_time = time.time() - start_time

            if elapsed_time > time_out:
                print("timeout")
                break

            if decoded_data.startswith(status_prefix):
                # print("Status line received: %s" % decoded_data)
                try:
                    status = decoded_data[len(status_prefix):]
                    received_data = status
                    success = True
                    break
                except UnicodeDecodeError as e:
                    print("Decoding failed: %s", str(e))
                    error_message = "Decoding error: " + str(e)
                    break
            else:
                # print("This line is not a status line: %s" % decoded_data)
                continue

            

        return {
            "success": success,
            "data_received": received_data,
            "error": error_message
        }

    def rel_pos(self, pos):
        """
        Move the robot to a relative position.

        Args:
        - pos: Relative movement in millimeters. Positive values move the robot outwards, and negative values move the robot inwards.
        """

        self._data_msg["rel_pos"] = pos
        self.send_data(["rel_pos"])

    def abs_pos(self, pos):
        """
        Move the robot to an absolute position.

        Args:
        - pos: Absolute position value. Position limits are 1m to 20mm.
        """

        if pos < 1 or pos > 20:
            raise ValueError("Absolute position must be between 1 and 20mm.")
        else:
            self._data_msg["abs_pos"] = pos
            self.send_data(["abs_pos"])

    def run_to_slot(self, dir, speed):
        """
        !BETA!
        This funtion is not yet tested. Use with caution.

        Move the robot in a given direction and at a given speed until it reaches a slot.

        Args:
        - dir: Direction of movement.
        - speed: Speed of movement.
        """
        self._data_msg["run_to_slot"] = dir*speed
        self.send_data(["run_to_slot"])

    def stop(self):
        """
        Stop the robot's movement.
        """

        self._serial.flush()
        self._set_flag(flag="stop", value=1)
        self.send_data(["stop"])
        self._serial.flush()
        time.sleep(0.1)

    def set_micro_step(self, m_step):
        """
        Change the microstep setting of the robot. Valid values are 
        1: Full step (0.01 mm) 
        2: Half step (0.005 mm)
        8: 1/8 step (0.00125 mm)

        Args:
        - m_step: Microstepping value.
        """

        if m_step not in [1, 2, 8]:
            raise ValueError("Microstep value must be 1, 2 or 8.")
        
        else:
            self._data_msg["micro_step"] = int(m_step)
            self.send_data(["micro_step"])

    def set_amnesia(self, value):
        """
        Put the robot in amnesia mode. Available values are:
        1: Amnesia mode on (no movement after power on)
        0: Amnesia mode off (Continues previous movement after power on)

        Args:
        - value: Amnesia value.
        """
        if value not in [0, 1]:
            raise ValueError("Amnesia value must be 0 or 1.")
        
        else:
            self._data_msg["amnesia"] = int(value)
            self.send_data(["amnesia"])

    def _set_flag(self, flag, value, send_data=False):
        """
        Set a specific flag value for the robot.

        Args:
        - flag: Flag to set.
        - value: Value to assign to the flag.
        - send_data: Boolean indicating whether to send the updated data.

        Returns:
        - Success status of flag setting.
        """

        try:
            if value:
                self._data_msg[flag] = int(1)
            else:
                self._data_msg[flag] = int(0)

            if send_data:
                self.send_data([flag])
        except KeyError:
            return 0
        return 1

    def connect(self):
        """
        Connect to the robot via the specified port and baudrate.
        """

        try:
            self._serial = serial.Serial(self.port, baudrate=self.baudrate, timeout=1)
            self._connected = True

        except serial.SerialException:
            self._connected = False

        return self._connected

    def is_connected(self):
        """
        Check if the robot is currently connected.

        Returns:
        - Connection status.
        """
        return self._connected

    def disconnect(self):
        """
        Disconnect from the robot.
        """

        if self._serial:
            self._serial.close()
            self._connected = False

    def send_all_data(self):
        """
        Send all data attributes to the robot.

        Raises:
        - ConnectionError if not connected to the robot.
        """

        if not self._connected:
            raise ConnectionError("Not connected to the robot. Connect first using connect() method.")

        json_data = json.dumps(self._data_msg) + '\n'
        self._serial.write(json_data.encode())

    def send_data(self, data_attributes):
        """
        Send specified data attributes to the robot.

        Args:
        - data_attributes: List of data attributes to send.

        Raises:
        - ConnectionError if not connected to the robot.
        """
        if not self._connected:
            raise ConnectionError("Not connected to the robot. Connect first using connect() method.")

        temp_data = {}
        for attribute in data_attributes:
            if attribute in self._data_msg:
                temp_data[attribute] = self._data_msg[attribute]
        json_data = json.dumps(temp_data) + '\n'
        self._serial.write(json_data.encode())

    def read_error(self, time_out=0.2):
        status_prefix = "***ERROR***"

        self._serial.flush()
        start_time = time.time()
        time.sleep(0.1)


        while True:
            raw_data = self._serial.readline()
            decoded_data = raw_data.decode().strip()  # Decode the bytes to a string and remove leading/trailing whitespace
            elapsed_time = time.time() - start_time

            if elapsed_time > time_out:
                # print("timeout")
                break

            if decoded_data.startswith(status_prefix):
                # print("Status line received: %s" % decoded_data)
                start_time = time.time()
                try:
                    status = decoded_data[len(status_prefix):]
                    print("Error: %s" % status)

                except UnicodeDecodeError as e:
                    print("Decoding failed: %s", str(e))
                    error_message = "Decoding error: " + str(e)

            else:
                # print("This line is not a status line: %s" % decoded_data)
                continue



