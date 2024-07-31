import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QSlider, QTextEdit, QGroupBox, \
    QRadioButton, QButtonGroup, QHBoxLayout, QWidget, QComboBox

from PyQt6.QtWidgets import QCheckBox, QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtGui import QGuiApplication

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QColor
from SpiraAPI import SpiraBot
from serial.tools import list_ports


class QuestionPopup(QDialog):
    def __init__(self, parent=None):
        super(QuestionPopup, self).__init__(parent)
        layout = QVBoxLayout()
        label = QLabel("If Amnesia is disabled, Spirabot starts simulating the with the last settings before it where shut down.", self)
        closeButton = QPushButton("Close", self)
        closeButton.clicked.connect(self.close)
        layout.addWidget(label)
        layout.addWidget(closeButton)
        self.setLayout(layout)

        # Set the dimensions of the popup and its position
        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('Information')
        self.center()

    def center(self):
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(
            (screen_geometry.width() - self.width()) // 2,
            (screen_geometry.height() - self.height()) // 2,
            self.width(),
            self.height()
        )


class CustomSlider(QSlider):
    def __init__(self, *args, **kwargs):
        super(CustomSlider, self).__init__(*args, **kwargs)
        self.mark_position = (7.12/19)  # Mark position in percentage (0-1)
        self.mark_position_end = (7.62/19)

    def paintEvent(self, event):
        super(CustomSlider, self).paintEvent(event)

        painter = QPainter(self)
        painter_end = QPainter(self)
        # painter.setPen(QPen(Qt.GlobalColor.Red, 2, Qt.PenStyle.SolidLine))
        painter.setPen(QPen(QColor(255, 0, 0), 2, Qt.PenStyle.SolidLine))
        painter_end.setPen(QPen(QColor(255, 0, 0), 2, Qt.PenStyle.SolidLine))

        mark_pixel = self.mark_position * self.width()
        mark_pixel_end = self.mark_position_end * self.width()
        painter.drawLine(mark_pixel, 0, mark_pixel, self.height())
        painter_end.drawLine(mark_pixel_end, 0, mark_pixel_end, self.height())


class RobotGui(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create layout and widgets
        layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.command_display = QTextEdit(self)
        self.command_display.setReadOnly(True)

        self.ports_combo = QComboBox(self)
        self.connect_button = QPushButton("Connect")

        self.amplitude_label = QLabel(self)
        self.amplitude_diff_label = QLabel(self)
        self.rpm_label = QLabel(self)
        self.amplitude_min_slider = QSlider(Qt.Orientation.Horizontal)
        self.amplitude_max_slider = QSlider(Qt.Orientation.Horizontal)
        self.amplitude_origo_slider = CustomSlider(Qt.Orientation.Horizontal)

        for port in list_ports.comports():
            self.ports_combo.addItem(port.device)

        self.amplitude_min_slider.setRange(1, 200)
        self.amplitude_max_slider.setRange(1, 200)
        self.amplitude_origo_slider.setRange(2, 400)  # Doubled for 0.5 steps

        self.amplitude_min_slider.setValue(50)
        self.amplitude_max_slider.setValue(150)
        self.amplitude_origo_slider.setValue(200)  # Adjusted for 0.5 steps

        self.rpm_input = QSlider(Qt.Orientation.Horizontal)
        self.rpm_input.setRange(0, 140)
        self.rpm_input.setValue(12)

        self.amnesia_checkbox = QCheckBox("Amnesia", self)
        self.amnesia_checkbox.setChecked(True)
        self.amnesia_checkbox.setEnabled(False)
        # Create clickable question mark next to the checkbox
        self.question_button = QPushButton("?", self)
        self.question_button.setMaximumWidth(30)
        self.question_button.clicked.connect(self.show_question_popup)

        microstep_groupbox = QGroupBox("Microstep Setting")
        microstep_layout = QVBoxLayout()
        self.microstep_1 = QRadioButton("1/1")
        self.microstep_2 = QRadioButton("1/2")
        self.microstep_8 = QRadioButton("1/8")
        self.microstep_8.setChecked(True)

        status_groupbox = QGroupBox("Status")
        status_layout = QVBoxLayout()
        self.position_button = QPushButton("Position")
        self.firmware_button = QPushButton("Firmware")
        status_layout.addWidget(self.position_button)
        status_layout.addWidget(self.firmware_button)
        status_groupbox.setLayout(status_layout)


        microstep_layout.addWidget(self.microstep_1)
        microstep_layout.addWidget(self.microstep_2)
        microstep_layout.addWidget(self.microstep_8)
        microstep_groupbox.setLayout(microstep_layout)

        self.microstep_group = QButtonGroup()
        self.microstep_group.addButton(self.microstep_1, 1)
        self.microstep_group.addButton(self.microstep_2, 2)
        self.microstep_group.addButton(self.microstep_8, 3)

        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.init_button = QPushButton("Init")
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.init_button)

        # Connect signals to slots
        self.start_button.clicked.connect(self.start_command)
        self.stop_button.clicked.connect(self.stop_robot)
        self.init_button.clicked.connect(self.init_command)
        self.position_button.clicked.connect(self.position_command)
        self.firmware_button.clicked.connect(self.firmware_command)
        self.microstep_group.idClicked.connect(self._microstep_command)
        self.amplitude_min_slider.valueChanged.connect(self.update_amplitude_label)
        self.amplitude_max_slider.valueChanged.connect(self.update_amplitude_label)
        self.amplitude_origo_slider.valueChanged.connect(self.update_amplitude_by_origo)
        self.rpm_input.valueChanged.connect(self.update_rpm_label)
        self.connect_button.clicked.connect(self.connect_to_robot)
        self.amnesia_checkbox.stateChanged.connect(self.on_amnesia_checkbox_toggle)

        # Add widgets to the layout
        layout.addWidget(self.command_display)
        layout.addWidget(QLabel("Select USB Port"))
        layout.addWidget(self.ports_combo)
        layout.addWidget(self.connect_button)
        # layout.addWidget(QLabel("Amplitude"))
        layout.addWidget(self.amplitude_label)
        layout.addWidget(self.amplitude_min_slider)
        layout.addWidget(self.amplitude_origo_slider)
        layout.addWidget(self.amplitude_max_slider)
        # layout.addWidget(QLabel("RPM"))
        layout.addWidget(self.rpm_label)
        layout.addWidget(self.rpm_input)
        layout.addWidget(microstep_groupbox)
        layout.addWidget(status_groupbox)
        layout.addWidget(self.amnesia_checkbox)
        layout.addWidget(self.question_button)
        layout.addLayout(button_layout)

        # Set up robot instance (initially None, set when "Connect" is clicked)
        self.robot = None
        self.update_amplitude_label()
        self.update_rpm_label()

    def show_question_popup(self):
        self.popup = QuestionPopup(self)
        self.popup.exec()

    def on_amnesia_checkbox_toggle(self, state):
        if self.robot:
            if state == Qt.CheckState.Checked:
                self.robot.set_flag("amnesia", 1, True)
                self.command_display.append(f"Amnesia activated.")
            else:
                self.robot.set_flag("amnesia", 0, True)
                self.command_display.append(f"Amnesia deactivated.")

    def connect_to_robot(self):
        port = self.ports_combo.currentText()
        self.robot = SpiraBot(port=port)
        while not self.robot.is_connected():
            connected = self.robot.connect()
            if connected:
                self.command_display.append(f"Successfully connected to port: {port}")
                self.amnesia_checkbox.setEnabled(True)
                self.robot.set_flag("amnesia", int(1), True)
                self.command_display.append(f"Amnesia activated.")
                status_msg = self.robot.status()
                self.command_display.append(f"Status_msg: {status_msg}")
                self.update_amplitude_label()
            else:
                self.command_display.append(f"Trying to connect to port: {port}...")

    def position_command(self):
        if self.robot:
            pos = self.robot.status(variable="current_pos")
            self.command_display.append(f"Current position: {pos}mm")

    def firmware_command(self):
        if self.robot:
            fw_version = self.robot.status(variable="fw_hash")
            self.command_display.append(f"Firmware version: {fw_version}")
    def start_command(self):
        amp_min = self.amplitude_min_slider.value()
        amp_max = self.amplitude_max_slider.value()
        amplitude = ((amp_max - amp_min) / 2)/10

        if self.robot:
            if check_action_validity(rpm=self.rpm_input.value(), micro_step=self.robot.get_micro_step(), amp=amplitude):
                self.robot.start_sine(amplitude, self.rpm_input.value())
                self.command_display.append(
                    f"Sent start_sine command with amplitude: {amplitude} and RPM: {self.rpm_input.value()} "
                    f"({rpm_to_hz(self.rpm_input.value())} Hz).")
            else:
                self.command_display.append(f"Unvalid values..")

    def init_command(self):
        if self.robot:
            self.robot.init()
            self.command_display.append(f"Sent init command.")

    def _microstep_command(self):
        if self.robot:
            microstep = self.microstep_group.checkedId()
            if microstep == 1:
                self.robot.set_micro_step(1)
                self.command_display.append(f"Sent set_micro_step command with value: 1/1.")
            elif microstep == 2:
                self.robot.set_micro_step(2)
                self.command_display.append(f"Sent set_micro_step command with value: 1/2.")
            elif microstep == 3:
                self.robot.set_micro_step(8)
                self.command_display.append(f"Sent set_micro_step command with value: 1/8.")

    def stop_robot(self):
        if self.robot:
            self.robot.stop()
            self.command_display.append(f"Sent stop command.")

    def update_rpm_label(self):
        rpm_value = str(self.rpm_input.value())
        self.rpm_label.setText(f"RPM: {rpm_value}")

    def update_amplitude_label(self):
        amp_range = (self.amplitude_min_slider.value(), self.amplitude_max_slider.value())
        if self.robot:
            self.robot.abs_pos(self.amplitude_min_slider.value()/10.0)
        self.amplitude_label.setText(f"Amplitude range: {amp_range[0]/10.0}mm - {amp_range[1]/10.0}mm ({format(amp_range[1]/10.0 - amp_range[0]/10.0, '.1f')}mm)")

        # Ensure min slider is not above max slider
        if self.amplitude_min_slider.value() > self.amplitude_max_slider.value():
            self.amplitude_min_slider.setValue(self.amplitude_max_slider.value())

        # Ensure max slider is not below min slider
        if self.amplitude_max_slider.value() < self.amplitude_min_slider.value():
            self.amplitude_max_slider.setValue(self.amplitude_min_slider.value())

        self.update_origo_slider()

    def update_origo_slider(self):
        avg = (self.amplitude_min_slider.value() + self.amplitude_max_slider.value()) * 2 // 2
        self.amplitude_origo_slider.blockSignals(True)
        self.amplitude_origo_slider.setValue(avg)
        self.amplitude_origo_slider.blockSignals(False)

        # Ensure origo slider is between min and max sliders
        if self.amplitude_origo_slider.value() < self.amplitude_min_slider.value() * 2:
            self.amplitude_origo_slider.setValue(self.amplitude_min_slider.value() * 2)
        if self.amplitude_origo_slider.value() > self.amplitude_max_slider.value() * 2:
            self.amplitude_origo_slider.setValue(self.amplitude_max_slider.value() * 2)

    def update_amplitude_by_origo(self):
        diff = (self.amplitude_max_slider.value() - self.amplitude_min_slider.value()) / 2
        origo = self.amplitude_origo_slider.value() / 2

        new_min = origo - diff
        new_max = origo + diff

        if new_min < 0:
            new_min = 0
            new_max = 2 * diff

        if new_max > 200:
            new_max = 200
            new_min = new_max - 2 * diff

        self.amplitude_min_slider.blockSignals(True)
        self.amplitude_max_slider.blockSignals(True)
        self.amplitude_min_slider.setValue(new_min)
        self.amplitude_max_slider.setValue(new_max)
        self.amplitude_min_slider.blockSignals(False)
        self.amplitude_max_slider.blockSignals(False)
        self.update_amplitude_label()


def rpm_to_hz(rpm):
    return rpm/60


def check_action_validity(rpm, micro_step, amp):
    if micro_step*amp > 24:
        return False

    if rpm > 30:
        if amp > 2.5:
            return False
    if rpm > 45:
        if amp > 2:
            return False

    if rpm > 60:
        if amp > 1:
            return False

    return True




app = QApplication(sys.argv)
window = RobotGui()
window.show()
sys.exit(app.exec())
