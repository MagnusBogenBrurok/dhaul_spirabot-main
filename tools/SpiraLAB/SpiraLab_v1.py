import os
import sys
import json
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QComboBox, QPushButton, QMessageBox, \
    QHBoxLayout, QLineEdit, QSlider, QFrame, QCheckBox, QGroupBox
from PyQt6.QtGui import QIcon, QColor, QPixmap
from PyQt6.QtCore import Qt, QSize
from PyQt6 import QtCore
import serial.tools.list_ports
import serial
from wave_form import*


# sys.stdout = open('output_log.txt', 'w')

root_path = os.path.dirname(os.path.abspath(__file__))

config_data = {
      "amplitude": 2,
      "start": 0,
      "init": 0,
      "stop": 1,
      "speed": 100,
      "calibration": 0,
      "inhale_acc": 3,
      "exhale_acc": 3,
      "origo": 11,
      "start_with_exhale": 0,
      "handshake": 1,
      "micro_step": 1
    }


class WelcomeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Welcome")
        self.setGeometry(200, 200, 300, 200)  # Increased the height to accommodate the input field
        background_color = QColor(24, 30, 39)  # Red color (adjust RGB values as needed)
        self.setStyleSheet(f"background-color: {background_color.name()};")

        self.sub_windows = []

        layout = QVBoxLayout()

        label = QLabel("Welcome to SpiraLAB")
        logo_label = QLabel()
        # Load the logo image
        pixmap = QPixmap("images/SpiraLab_front_page_logo.png")

        # Set the image pixmap
        logo_label.setPixmap(pixmap)

        # Set the alignment within the label
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add the label to the layout
        layout.addWidget(logo_label)
        layout.addWidget(label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter window name")
        layout.addWidget(self.name_input)

        self.add_button = QPushButton("Add SpiraBot")
        self.add_button.setStyleSheet("QPushButton { background-color: white; color: black; }")
        self.add_button.clicked.connect(self.open_new_instance)
        layout.addWidget(self.add_button)

        self.new_instance = None  # Store the new instance as a member variable

        self.setLayout(layout)

    def open_new_instance(self):
        window_name = self.name_input.text()
        if window_name:
            new_instance = MyWindow(title=window_name)  # Assign the new instance to the member variable
            self.sub_windows.append(new_instance)
            new_instance.show()


def calculate_scaled_size(original_size, target_width):
    aspect_ratio = original_size.width() / original_size.height()
    scaled_height = int(target_width / aspect_ratio)
    return QSize(target_width, scaled_height)


class MyWindow(QWidget):
    def __init__(self, title):
        self.connected = False
        # Load the configuration from the file
        # Access the data and command list
        self.data = config_data
        self.data["stop"] = int(1)
        self.serial = ""
        super().__init__()
        self.setWindowTitle(title)
        background_color = QColor(24, 30, 39)  # Red color (adjust RGB values as needed)
        self.setStyleSheet(f"background-color: {background_color.name()};")
        self.setGeometry(200, 200, 600, 500)

        # Create a dropdown menu
        # self.dropdown = QComboBox(self)
        # self.dropdown.setStyleSheet(f"QComboBox background-color: {background_color}; color: white")

        # Get a list of available USB ports
        self.ports = self.get_available_ports()

        # Populate the dropdown menu with the port names
        # self.populate_dropdown()
        # self.dropdown.currentIndexChanged.connect(self.connect_to_port)

        self.spira_label = QLabel("Select SpiraBot")

        # Create a Refresh button
        self.refresh_button = QPushButton("Refresh", self)
        self.refresh_button.setStyleSheet("QPushButton { background-color: white; color: black; }")
        self.refresh_button.clicked.connect(self.refresh_ports)

        self.checkbox = QCheckBox("Start with exhale")
        self.checkbox.stateChanged.connect(self.checkbox_state_changed)
        self.checkbox.setChecked(False)

        self.micro_step_checkbox1 = QCheckBox("Full stepping")
        self.micro_step_checkbox1.stateChanged.connect(self.micro_step_checkbox1_state_changed)
        self.micro_step_checkbox1.setChecked(False)

        self.micro_step_checkbox2 = QCheckBox("Micro stepping (1/2)")
        self.micro_step_checkbox2.stateChanged.connect(self.micro_step_checkbox2_state_changed)
        self.micro_step_checkbox2.setChecked(False)

        self.micro_step_checkbox8 = QCheckBox("Micro stepping (1/8)")
        self.micro_step_checkbox8.stateChanged.connect(self.micro_step_checkbox8_state_changed)
        self.micro_step_checkbox8.setChecked(False)

        # Create sliders for amplitude
        self.amp_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.amp_slider.setMinimum(1)
        self.amp_slider.setMaximum(10)
        self.amp_slider.setValue(2)
        self.amp_slider.valueChanged.connect(self.update_amp_label)

        # Create slider for speed
        self.speed_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.speed_slider.setMinimum(1)
        self.speed_slider.setMaximum(500)
        self.speed_slider.setValue(100)
        self.speed_slider.valueChanged.connect(self.update_speed_label)

        # Create slider for inhale acc
        self.inhale_acc_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.inhale_acc_slider.setMinimum(1)
        self.inhale_acc_slider.setMaximum(8)
        self.inhale_acc_slider.setValue(3)
        self.inhale_acc_slider.valueChanged.connect(self.update_inhale_acc_label)

        # Create slider for exhale acc
        self.exhale_acc_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.exhale_acc_slider.setMinimum(1)
        self.exhale_acc_slider.setMaximum(8)
        self.exhale_acc_slider.setValue(3)
        self.exhale_acc_slider.valueChanged.connect(self.update_exhale_acc_label)

        # Create slider for Origo
        self.origo_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.origo_slider.setMinimum(1)
        self.origo_slider.setMaximum(25)
        self.origo_slider.setValue(11)
        self.origo_slider.valueChanged.connect(self.update_origo_label)

        # Create labels for amplitude and speed values
        self.freq_label = QLabel("RPM: 0", self)
        self.amp_label = QLabel("Amplitude: 2", self)
        self.speed_label = QLabel("Speed: 100", self)

        # Create labels for accelerations
        self.inhale_acc_label = QLabel("Inhale acceleration: 3", self)
        self.exhale_acc_label = QLabel("Exhale acceleration: 3", self)

        self.origo_label = QLabel("Origo: 11 mm", self)

        self.line = QFrame()
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        # Create a Start/Stop button
        icon_size = QtCore.QSize(50, 50)
        self.stop_button = QPushButton(self)
        self.stop_button.setStyleSheet("QPushButton { border: none; background-color: transparent; }")
        self.stop_icon = QIcon(os.path.join(root_path, "images", "stop-squared.png"))
        self.start_icon = QIcon(os.path.join(root_path, "images", "circled-play.png"))
        self.stop_button.setIcon(self.start_icon)
        self.stop_button.setIconSize(icon_size)
        self.stop_button.clicked.connect(self.do_stop_button)
        self.stop_button.setEnabled(False)

        # Create a Init button
        self.icon_size = QtCore.QSize(50, 50)
        self.init_button = QPushButton(self)
        self.init_button.setStyleSheet("QPushButton { border: none; background-color: transparent; }")
        self.init_icon = QIcon(os.path.join(root_path, "images", "skip-to-start.png"))
        self.init_button.setIcon(self.init_icon)
        self.init_button.setIconSize(self.icon_size)
        self.init_button.clicked.connect(self.do_init_button)
        self.init_button.setEnabled(False)

        self.advanced_button = QPushButton("Advanced")
        self.advanced_button.setCheckable(True)
        self.advanced_button.setChecked(False)
        self.advanced_button.toggled.connect(self.toggle_advanced_settings)

        # Create a layout for the sliders and labels
        slider_layout = QVBoxLayout()
        slider_layout.addWidget(self.freq_label)
        slider_layout.addWidget(self.amp_label)
        slider_layout.addWidget(self.amp_slider)
        slider_layout.addWidget(self.speed_label)
        slider_layout.addWidget(self.speed_slider)

        # Create a layout for the connect button, start button, stop button, and send button
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.init_button)
        button_layout.addWidget(self.stop_button)

        self.port_layout = QVBoxLayout()

        self.spira_on_icon = QIcon(os.path.join(root_path, "images", "SpiraBot_Icon_on.png"))
        self.spira_off_icon = QIcon(os.path.join(root_path, "images", "SpiraBot_Icon_off.png"))

        self.port_buttons = []
        self.selected_port = None
        port_nr = 0
        self.populate_port_buttons()


        # Set the layout for the main window
        layout = QVBoxLayout()
        # layout.addWidget(self.dropdown)
        layout.addWidget(self.spira_label)
        layout.addLayout(self.port_layout)
        layout.addWidget(self.refresh_button)
        layout.addLayout(slider_layout)
        layout.addLayout(button_layout)
        layout.addWidget(self.advanced_button)
        layout.addSpacing(30)

        self.advanced_groupbox = QGroupBox("Advanced Settings")
        self.advanced_groupbox.setFlat(True)
        layout.addWidget(self.advanced_groupbox)

        self.advanced_layout = QVBoxLayout()
        self.advanced_groupbox.setLayout(self.advanced_layout)
        self.advanced_layout.addWidget(self.exhale_acc_label)
        self.advanced_layout.addWidget(self.exhale_acc_slider)
        self.advanced_layout.addWidget(self.inhale_acc_label)
        self.advanced_layout.addWidget(self.inhale_acc_slider)
        self.advanced_layout.addWidget(self.origo_label)
        self.advanced_layout.addWidget(self.origo_slider)
        self.advanced_layout.addWidget(self.checkbox)
        self.advanced_layout.addWidget(self.micro_step_checkbox1)
        self.advanced_layout.addWidget(self.micro_step_checkbox2)
        self.advanced_layout.addWidget(self.micro_step_checkbox8)

        self.advanced_groupbox.setVisible(False)

        # Set the layout for the main window
        self.setLayout(layout)

        self.reset_all()

    def reset_all(self):
        self.reset_data()
        self.origo_slider.setValue(self.data["origo"])
        self.origo_label.setText("Origo: {}".format(self.data["origo"]) + " mm")

        self.exhale_acc_slider.setValue(self.data["exhale_acc"])
        self.exhale_acc_label.setText("Exhale acceleration: {}".format(self.data["exhale_acc"]))

        self.inhale_acc_slider.setValue(self.data["inhale_acc"])
        self.inhale_acc_label.setText("Inhale acceleration: {}".format(self.data["inhale_acc"]))

        self.speed_slider.setValue(self.data["speed"])
        self.speed_label.setText("Speed: {}".format(self.data["speed"]))

        self.amp_slider.setValue(self.data["amplitude"])
        self.amp_label.setText("Amplitude: {}".format(self.data["amplitude"]))

    def checkbox_state_changed(self, state):
        if state == 2:  # Checked state
            print("Checkbox is checked")
            self.data["start_with_exhale"] = int(1)
            # Perform actions for checked state
        else:  # Unchecked state
            print("Checkbox is unchecked")
            self.data["start_with_exhale"] = int(0)
            # Perform actions for unchecked state

        self.send_serial_message()

    def micro_step_checkbox1_state_changed(self, state):
        if state == 2:
            print("Checkbox 1 is checked")
            self.micro_step_checkbox2.setChecked(False)
            self.micro_step_checkbox8.setChecked(False)
            self.data["micro_step"] = int(1)
        else:
            print("Checkbox 1 is unchecked")

    def micro_step_checkbox2_state_changed(self, state):
        if state == 2:
            print("Checkbox 2 is checked")
            self.micro_step_checkbox1.setChecked(False)
            self.micro_step_checkbox8.setChecked(False)
            self.data["micro_step"] = int(2)
        else:
            print("Checkbox 2 is unchecked")

    def micro_step_checkbox8_state_changed(self, state):
        if state == 2:
            print("Checkbox 3 is checked")
            self.micro_step_checkbox1.setChecked(False)
            self.micro_step_checkbox2.setChecked(False)
            self.data["micro_step"] = int(8)
        else:
            print("Checkbox 3 is unchecked")

        # if state == 2:  # Checked state
        #    print("micro_step Checkbox is checked")
        #    self.data["micro_step"] = int(1)
        #    # Perform actions for checked state
        # else:  # Unchecked state
        #    print("micro_step Checkbox is unchecked")
        #    self.data["micro_step"] = int(0)
            # Perform actions for unchecked state

        self.send_serial_message()

    def toggle_advanced_settings(self, checked):
        # Show or hide the advanced settings based on the button state
        self.advanced_groupbox.setVisible(checked)

    def get_available_ports(self):
        # Retrieve a list of available USB ports
        ports = []
        available_ports = serial.tools.list_ports.comports()
        for port in available_ports:
            if "USB" in port.description:  # Check if the port description contains "USB"
                ports.append(port.device)

        return ports

    def populate_port_buttons(self):
        # Clear the layout containing the port buttons
        for i in reversed(range(self.port_layout.count())):
            self.port_layout.itemAt(i).widget().setParent(None)

        # Create and populate the port buttons based on the available ports
        self.ports = self.get_available_ports()
        self.port_buttons = []
        for port in self.ports:
            port_button = QPushButton(port, self)
            port_button.setIcon(self.spira_off_icon)
            port_button.setIconSize(self.icon_size)
            port_button.setStyleSheet("QPushButton { border: none; background-color: transparent; }")
            port_button.setFixedSize(QSize(250, 100))
            port_button.clicked.connect(self.connect_to_port)
            self.port_buttons.append(port_button)
            self.port_layout.addWidget(port_button)

        if len(self.port_buttons) == 0:
            self.spira_label.setText("No SpiraBots detected..")

        else:
            self.spira_label.setText("Select SpiraBot:")

    def refresh_ports(self):
        print("refresh_button pushed")
        # Refresh the list of available USB ports
        self.ports = self.get_available_ports()
        self.populate_port_buttons()
        self.connected = False
        self.serial = ""

    def do_stop_button(self):
        print("Stop button clicked")
        if self.data["stop"]:
            self.data["stop"] = int(0)
            self.data["start"] = int(1)
            self.stop_button.setIcon(self.stop_icon)
        else:
            self.data["stop"] = int(1)
            self.data["start"] = int(0)
            self.stop_button.setIcon(self.start_icon)
        self.send_serial_message()

    def do_init_button(self):
        print("init button clicked")
        self.data["init"] = int(1)
        self.send_serial_message()

    def connect_to_port(self):
        # Get the selected port from the button text
        selected_port = self.sender().text()
        port_index = 0
        for p in self.port_buttons:
            if p.text() == selected_port:
                break
            port_index += 1

        try:
            # Create a serial connection
            self.serial = serial.Serial(selected_port, baudrate=115200)
            self.stop_button.setEnabled(True)
            self.init_button.setEnabled(True)
            self.port_buttons[port_index].setIcon(self.spira_on_icon)
            self.port_buttons[port_index].setEnabled(False)
            self.connected = True
            self.reset_all()
            self.send_serial_message()
        except serial.SerialException:
            QMessageBox.warning(self, "Connection Error", "Failed to connect to {}".format(selected_port))

    def send_serial_message(self):

        print(self.data)
        # Create a JSON object with name and age
        json_data = json.dumps(self.data) + '\n'

        # Send the JSON object to the connected port
        try:
            self.serial.write(json_data.encode())
            # QMessageBox.information(self, "Message Sent", "Message sent successfully!")
        except AttributeError:
            QMessageBox.warning(self, "Send Error", "No port connected. Connect to a port first.")

        rpm = calculate_rpm(self.data)
        self.freq_label.setText("RPM: {}".format(rpm))
        self.data["init"] = ""

    def reset_data(self):
        self.data = config_data

    def update_amp_label(self):
        # Update the amplitude label
        amp_value = self.amp_slider.value()
        self.data["amplitude"] = int(amp_value)
        self.amp_label.setText("Amplitude: {}".format(amp_value))
        self.send_serial_message()

    def update_speed_label(self):
        # Update the speed label
        speed_value = self.speed_slider.value()
        self.data["speed"] = int(speed_value)
        self.speed_label.setText("Speed: {}".format(speed_value))
        self.send_serial_message()

    def update_inhale_acc_label(self):
        # Update the inhale acceleration label
        inhale_acc_value = self.inhale_acc_slider.value()
        self.data["inhale_acc"] = int(inhale_acc_value)
        self.inhale_acc_label.setText("Inhale acceleration: {}".format(inhale_acc_value))
        self.send_serial_message()

    def update_exhale_acc_label(self):
        # Update the exhale acceleration label
        exhale_acc_value = self.exhale_acc_slider.value()
        self.data["exhale_acc"] = int(exhale_acc_value)
        self.exhale_acc_label.setText("Exhale acceleration: {}".format(exhale_acc_value))
        self.send_serial_message()

    def update_origo_label(self):
        # Update the amplitude label
        origo_value = self.origo_slider.value()
        self.data["origo"] = int(origo_value)
        self.origo_label.setText("Origo: {}".format(origo_value) + "mm")
        self.send_serial_message()


def calculate_rpm(robot_config):
    time_elapsed = 0
    step_length_mm = 0.01/robot_config["micro_step"]
    total_steps = robot_config["amplitude"]/step_length_mm
    spot_freq = robot_config["speed"]*robot_config["micro_step"]
    # Inhale phase
    acc_steps = int(total_steps/3)
    for acc in range(1, acc_steps):
        time_elapsed += 1/spot_freq
        spot_freq += robot_config["inhale_acc"]

    for lin in range(1, acc_steps):
        time_elapsed += 1/spot_freq

    spot_freq += 1

    for dec in range(1, acc_steps):
        time_elapsed += 1 / spot_freq
        spot_freq -= robot_config["inhale_acc"]

    # Exnhale phase
    acc_steps = int(total_steps / 3)
    spot_freq = robot_config["speed"]*robot_config["micro_step"]
    for acc in range(1, acc_steps):
        time_elapsed += 1 / spot_freq
        spot_freq += robot_config["exhale_acc"]

    for lin in range(1, acc_steps):
        time_elapsed += 1 / spot_freq

    spot_freq += 1

    for dec in range(1, acc_steps):
        time_elapsed += 1 / spot_freq
        spot_freq -= robot_config["inhale_acc"]
    if time_elapsed:
        rpm = 60/time_elapsed
        return format(rpm, ".2f")
    else:
        return 0


if __name__ == '__main__':
    app = QApplication(sys.argv)

    welcome_window = WelcomeWindow()
    welcome_window.show()

    sys.exit(app.exec())
