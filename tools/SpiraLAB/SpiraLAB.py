import os
import sys
import json
import math
import numpy as np
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QComboBox, QPushButton, QMessageBox, \
    QHBoxLayout, QSlider, QRadioButton, QFileDialog, QSpinBox, QDoubleSpinBox
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, QSize
import serial.tools.list_ports
import serial
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.backend_bases import MouseEvent

root_path = os.path.dirname(os.path.abspath(__file__))

data = {
    "start": 0,
    "init": 0,
    "stop": 0,
    "loop_count": -1,
    "origo": 11,
    "micro_step": 1,
    "freq": 17,
    "curve_length": 86,
    "curve": [],
}

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self._dragging_point = None
        self._line = None
        super(MplCanvas, self).__init__(self.fig)

class CurveGenerator(QWidget):
    def __init__(self, parent=None):
        super(CurveGenerator, self).__init__(parent)
        self.setWindowTitle("Create new Curve")
        self.setMinimumSize(700, 640)
        self.load_button_active = False

        self.STEPS_PER_MM = 100
        self.length_s = 5
        self.amplitude_mm = 2
        self.rpm = 12
        self.sample_frequency_hz = 10

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.sc = MplCanvas(self, width=5, height=4, dpi=100)
        self.sc.fig.canvas.mpl_connect('button_press_event', self._on_click)
        self.sc.fig.canvas.mpl_connect('button_release_event', self._on_release)
        self.sc.fig.canvas.mpl_connect('motion_notify_event', self._on_motion)
        self.generate_input_wave()
        self.update_plot()
        toolbar = NavigationToolbar(self.sc, self)
        layout.addWidget(toolbar)
        layout.addWidget(self.sc)

        length_layout = QHBoxLayout()
        length_label = QLabel("Length [s]:")
        length_label.setFixedWidth(125)
        length_layout.addWidget(length_label)
        self.length_input = QDoubleSpinBox()
        self.length_input.setMinimum(1)
        self.length_input.setMaximum(120)
        self.length_input.setSingleStep(1)
        self.length_input.setValue(self.length_s)
        self.length_input.valueChanged.connect(self.set_length)
        self.length_input.setEnabled(True)
        length_layout.addWidget(self.length_input, 1)
        layout.addLayout(length_layout)

        amplitude_layout = QHBoxLayout()
        amplitude_label = QLabel("Amplitude [mm]:")
        amplitude_label.setFixedWidth(125)
        amplitude_layout.addWidget(amplitude_label)
        self.amplitude_input = QSpinBox()
        self.amplitude_input.setMinimum(1)
        self.amplitude_input.setMaximum(5)
        self.amplitude_input.setValue(self.amplitude_mm)
        self.amplitude_input.valueChanged.connect(self.set_amplitude)
        amplitude_layout.addWidget(self.amplitude_input, 1)
        layout.addLayout(amplitude_layout)

        rpm_layout = QHBoxLayout()
        rpm_label = QLabel("RPM:")
        rpm_label.setFixedWidth(125)
        rpm_layout.addWidget(rpm_label)
        self.rpm_input = QSpinBox()
        self.rpm_input.setMinimum(2)
        self.rpm_input.setMaximum(60)
        self.rpm_input.setValue(self.rpm)
        self.rpm_input.valueChanged.connect(self.set_rpm)
        self.rpm_input.setEnabled(True)
        rpm_layout.addWidget(self.rpm_input, 1)
        layout.addLayout(rpm_layout)

        sample_frequency_layout = QHBoxLayout()
        sample_frequency_label = QLabel("Sample frequency [Hz]:")
        sample_frequency_label.setFixedWidth(125)
        sample_frequency_layout.addWidget(sample_frequency_label)
        self.sample_frequency_input = QSpinBox()
        self.sample_frequency_input.setMinimum(1)
        self.sample_frequency_input.setMaximum(30)
        self.sample_frequency_input.setValue(self.sample_frequency_hz)
        self.sample_frequency_input.valueChanged.connect(self.set_sample_frequency)
        sample_frequency_layout.addWidget(self.sample_frequency_input, 1)
        layout.addLayout(sample_frequency_layout)


        action_buttons = QHBoxLayout()

        self.upload_button = QPushButton("Upload curve")
        self.upload_button.clicked.connect(self.upload_to_device)
        action_buttons.addWidget(self.upload_button)

        self.save_button = QPushButton("Save to file")
        self.save_button.clicked.connect(self.save_to_file)
        action_buttons.addWidget(self.save_button)

        self.load_button = QPushButton("Load from file")
        self.load_button.clicked.connect(self.load_from_file)
        action_buttons.addWidget(self.load_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_curve)
        action_buttons.addWidget(self.reset_button)

        layout.addLayout(action_buttons)

    def _find_neighbor_point(self, event):
        u""" Find point around mouse position

        :rtype: ((int, int)|None)
        :return: (x, y) if there are any point around mouse else None
        """
        distance_threshold = 0.25
        nearest_point = None
        min_distance = math.sqrt(2 * (100 ** 2))
        i = 0
        while i < len(self.input_wave)-1:
            distance = math.hypot(event.xdata - self.time[i], event.ydata - self.input_wave[i])
            if distance < min_distance:
                min_distance = distance
                nearest_point = i
            i+=1
        if min_distance < distance_threshold:
            return nearest_point
        return None
    
    def _on_click(self, event):
        u""" callback method for mouse click event

        :type event: MouseEvent
        """
        # left click
        if event.button == 1 and event.inaxes in [self.sc.axes]:
            point = self._find_neighbor_point(event)
            if point:
                self.sc._dragging_point = point
            self.rpm_input.setEnabled(False)
            self.update_plot()

    def _on_release(self, event):
        u""" callback method for mouse release event

        :type event: MouseEvent
        """
        if event.button == 1 and event.inaxes in [self.sc.axes] and self.sc._dragging_point:
            self.sc._dragging_point = None
            self.update_plot()

    def _on_motion(self, event):
        u""" callback method for mouse motion event

        :type event: MouseEvent
        """
        if not self.sc._dragging_point:
            return
        if event.xdata is None or event.ydata is None:
            return
        self.input_wave[self.sc._dragging_point] = event.ydata
        self.update_plot()

    def generate_time_axis(self, length_s, sample_frequency_hz):
        self.time = []
        for t in np.arange(0, length_s+(1/sample_frequency_hz), (1/sample_frequency_hz)):
            self.time.append(round(t, 2))

    def generate_input_wave(self):
        self.generate_time_axis(self.length_s, self.sample_frequency_hz)
        self.input_wave=[]
        for t in self.time:
            self.input_wave.append(self.amplitude_mm * np.sin(2 * np.pi * t / (60/self.rpm)))
        self.input_wave[len(self.input_wave)-1] = 0.0


    def generate_output_wave(self):
        # Count the number of steps between each time step
        self.step_count = []
        prev_input_wave = 0
        i = 0
        step_overflow = 0
        for t in self.time:
            steps = self.STEPS_PER_MM*(self.input_wave[i] - prev_input_wave)
            if steps > 0:
                step_overflow += steps - math.floor(steps)
                if step_overflow >= 1:
                    self.step_count.append(math.floor(steps) + 1)
                    step_overflow -= 1
                else:
                    self.step_count.append(math.floor(steps))
            else:
                step_overflow += steps + math.floor(abs(steps))
                if step_overflow <= -1:
                    self.step_count.append(-math.floor(abs(steps)) - 1)
                    step_overflow += 1
                else:
                    self.step_count.append(-math.floor(abs(steps)))
            prev_input_wave = self.input_wave[i]
            i+=1

        # Compensate for rounding errors
        res = 0
        for i in range(len(self.step_count)):
            res += self.step_count[i]
        if res != 0:
            self.step_count[len(self.step_count)-1] -= res

        max_steps = 1200 / self.sample_frequency_hz
        overflow = 0
        for i in range(len(self.step_count)):
            if self.step_count[i] + overflow > max_steps:
                overflow += self.step_count[i] - max_steps
                self.step_count[i] = max_steps
            elif self.step_count[i] + overflow < -max_steps:
                overflow += self.step_count[i] + max_steps
                self.step_count[i] = -max_steps
            else:
                self.step_count[i] += overflow
                overflow = 0

        # Generate output wave from step count
        self.output_wave = []
        prev_output_wave = 0
        for i in range(len(self.step_count)):
            self.output_wave.append((self.step_count[i]/self.STEPS_PER_MM)+prev_output_wave)
            prev_output_wave = self.output_wave[i]
    
    def set_length(self, value):
        self.length_s = value
        self.length_input.setValue(self.length_s)
        if self.load_button_active == False:
            prev_input_wave = self.input_wave
            prev_input_wave.pop(len(prev_input_wave)-1)
            self.generate_input_wave()
            if len(prev_input_wave) > len(self.input_wave):
                self.input_wave = prev_input_wave[:len(self.input_wave)]
                self.input_wave[len(self.input_wave)-1] = 0.0
            else:
                self.input_wave[:len(prev_input_wave)] = prev_input_wave
        self.update_plot()
    
    def set_amplitude(self, value):
        self.amplitude_mm = value
        
        input_wave_max = 0
        for i in range(len(self.input_wave)):
            if abs(self.input_wave[i]) > input_wave_max:
                input_wave_max = abs(self.input_wave[i])
        if input_wave_max != self.amplitude_mm:
            k = self.amplitude_mm / input_wave_max
            for i in range(len(self.input_wave)):
                self.input_wave[i] *= k

        self.amplitude_input.setValue(round(self.amplitude_mm))
        self.update_plot()

    def set_rpm(self, value):
        self.rpm = value
        # self.set_sample_frequency(round(self.rpm/1.665))
        self.rpm_input.setValue(self.rpm)
        self.generate_input_wave()
        self.update_plot()

    def set_sample_frequency(self, value):
        if value == 0:
            return
        self.sample_frequency_hz = value
        self.sample_frequency_input.setValue(value)
        self.generate_input_wave()
        if self.load_button_active:
            self.set_length((len(self.input_wave)-1)/self.sample_frequency_hz)
            self.generate_time_axis((len(self.input_wave)-1)/self.sample_frequency_hz, self.sample_frequency_hz)
        self.update_plot()

    def update_plot(self):
        self.generate_output_wave()
        self.sc.axes.clear()
        self.sc.axes.plot(self.time, self.input_wave, color="blue", marker="o")
        self.sc.axes.plot(self.time, self.input_wave, label="Input", color="blue")
        self.sc.axes.plot(self.time, self.output_wave, label="Output", color="orange")
        self.sc.axes.set_xlabel("Time [s]")
        self.sc.axes.set_ylabel("Amplitude [mm]")
        self.sc.axes.legend()
        self.sc.axes.grid()
        self.sc.axes.set_ylim(-5, 5)
        self.sc.axes.set_xlim(min(self.time), max(self.time))
        self.sc.draw()

    def upload_to_device(self):
        data["freq"] = self.sample_frequency_hz
        data["curve_length"] = len(self.time)
        data["curve"] = self.step_count

    def load_from_file(self):
        self.load_button_active = True
        file_filter = 'Data File (*.xlsx *.csv *.txt);; Text file (*.txt)'
        response = QFileDialog.getOpenFileName(
            parent=self,
            caption='Select a file',
            directory=os.getcwd(),
            filter=file_filter,
            initialFilter='Data File (*.xlsx *.csv *.txt)'
        )
        if response[0] == "":
            return
        selected_file = open(str(response[0])).read()
        file_data = selected_file.splitlines()

        self.input_wave = [eval(i) for i in file_data]

        if len(self.input_wave) > 1200:
            QMessageBox.warning(self, "Error", "Curve length is too long. First 1200 elements imported.")
            self.generate_time_axis(119, 1)
            self.set_length(120)
            self.input_wave = self.input_wave[:1200]
        else:
            self.generate_time_axis((len(self.input_wave)-1)/10, 10)
            self.set_length(len(self.time)-(1/10))

        self.set_sample_frequency(10)
        self.input_wave[0] = 0.0
        self.input_wave[len(self.input_wave)-1] = 0.0
        
        input_wave_max = 0
        for i in range(len(self.input_wave)):
            if abs(self.input_wave[i]) > input_wave_max:
                input_wave_max = abs(self.input_wave[i])
        if abs(input_wave_max) > 5:
            self.set_amplitude(5)
        elif abs(input_wave_max) < 1:
            self.set_amplitude(1)

        self.length_input.setEnabled(False)
        self.rpm_input.setEnabled(False)
        
        self.update_plot()

    def save_to_file(self):
        file_filter = 'Data File (*.csv)'
        response = QFileDialog.getSaveFileName(
            parent=self,
            caption='Save file',
            directory=os.getcwd()+"/programs",
            filter=file_filter,
            initialFilter='Data File (*.csv)'
        )
        if response[0] == "":
            return
        with open(response[0], 'w') as f:
            f.write(str(self.sample_frequency_hz)+"\n")
            for i in self.step_count:
                f.write(str(i)+"\n")

    def reset_curve(self):
        self.load_button_active = False
        self.length_input.setEnabled(True)
        self.rpm_input.setEnabled(True)
        self.set_length(5)
        self.set_amplitude(2)
        self.set_rpm(12)
        self.update_plot()

class WindowInstance(QWidget):
    def __init__(self):
        self.connected = False
        self.serial = ""
        self.icon_size = QSize(50, 50)

        super().__init__()
        self.setWindowTitle("SpiraLAB")
        self.window_width, self.window_height = 400, 200
        self.setMinimumSize(self.window_width, self.window_height)

        layout = QVBoxLayout()
        self.setLayout(layout)


        self.ports = self.get_available_ports()
        self.ports.insert(0, '-- Select port --')
        self.port_combo_box = QComboBox()
        self.port_combo_box.addItems(self.ports)
        self.port_combo_box.currentIndexChanged.connect(self.connect_to_port)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_ports)

        ports_layout = QHBoxLayout()
        ports_layout.addWidget(self.port_combo_box, 1)
        ports_layout.addWidget(refresh_button, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(ports_layout)


        self.start_button = QPushButton(self)
        self.start_button.setIcon(QIcon(os.path.join(root_path, "images", "circled-play.png")))
        self.start_button.setIconSize(self.icon_size)
        self.start_button.clicked.connect(self.do_start_button)
        self.start_button.setEnabled(False)

        self.stop_button = QPushButton(self)
        self.stop_button.setIcon(QIcon(os.path.join(root_path, "images", "stop-squared.png")))
        self.stop_button.setIconSize(self.icon_size)
        self.stop_button.clicked.connect(self.do_stop_button)
        self.stop_button.setEnabled(False)

        self.init_button = QPushButton(self)
        self.init_button.setIcon(QIcon(os.path.join(root_path, "images", "skip-to-start.png")))
        self.init_button.setIconSize(self.icon_size)
        self.init_button.clicked.connect(self.do_init_button)
        self.init_button.setEnabled(False)

        control_buttons = QHBoxLayout()
        control_buttons.addWidget(self.init_button)
        control_buttons.addWidget(self.start_button)
        control_buttons.addWidget(self.stop_button)
        layout.addLayout(control_buttons)


        self.curve_button = QPushButton("New curve")
        self.curve_button.clicked.connect(self.show_curve_generator)
        self.curve_button.setEnabled(False)

        self.upload_button = QPushButton("Upload curve")
        self.upload_button.clicked.connect(self.read_from_file)
        self.upload_button.setEnabled(False)

        curve_buttons = QHBoxLayout()
        curve_buttons.addWidget(self.curve_button)
        curve_buttons.addWidget(self.upload_button)
        layout.addLayout(curve_buttons)

        self.settings_label = QLabel("Settings")

        loop_count_layout = QHBoxLayout()
        self.loop_count_label = QLabel("Loop count:", self)
        self.loop_count_label.setFixedWidth(65)
        loop_count_layout.addWidget(self.loop_count_label)
        self.loop_count_input = QSpinBox()
        self.loop_count_input.setMinimum(-1)
        self.loop_count_input.setMaximum(1000)
        self.loop_count_input.setValue(-1)
        self.loop_count_input.valueChanged.connect(self.set_loop_count)
        self.loop_count_input.setEnabled(False)
        loop_count_layout.addWidget(self.loop_count_input, 1)

        origo_layout = QHBoxLayout()
        self.origo_label = QLabel("Origin:", self)
        self.origo_label.setFixedWidth(65)
        origo_layout.addWidget(self.origo_label)
        self.origo_input = QSpinBox()
        self.origo_input.setMinimum(6)
        self.origo_input.setMaximum(18)
        self.origo_input.setValue(11)
        self.origo_input.valueChanged.connect(self.set_origo)
        self.origo_input.setEnabled(False)
        origo_layout.addWidget(self.origo_input, 1)

        micro_step_layout = QHBoxLayout()
        self.micro_step_1 = QRadioButton("Full stepping")
        self.micro_step_1.setChecked(True)
        self.micro_step_1.toggled.connect(lambda:self.btnstate(self.micro_step_1))
        self.micro_step_1.setEnabled(False)
        micro_step_layout.addWidget(self.micro_step_1)
        self.micro_step_2 = QRadioButton("Micro stepping (1/2)")
        self.micro_step_2.toggled.connect(lambda:self.btnstate(self.micro_step_2))
        self.micro_step_2.setEnabled(False)
        micro_step_layout.addWidget(self.micro_step_2)
        self.micro_step_8 = QRadioButton("Micro stepping (1/8)")
        self.micro_step_8.toggled.connect(lambda:self.btnstate(self.micro_step_8))
        self.micro_step_8.setEnabled(False)
        micro_step_layout.addWidget(self.micro_step_8)

        curve_widget = QWidget()
        self.curve_layout = QVBoxLayout()
        curve_widget.setLayout(self.curve_layout)
        self.curve_layout.addWidget(self.settings_label)
        self.curve_layout.addLayout(loop_count_layout)
        self.curve_layout.addLayout(origo_layout)
        self.curve_layout.addLayout(micro_step_layout)
        curve_widget.setStyleSheet(" border: 1px solid gray;")
        self.settings_label.setStyleSheet("border: 0; font-weight: bold;")
        self.loop_count_label.setStyleSheet("border: 0;")
        self.loop_count_input.setStyleSheet("border: 0;")
        self.origo_label.setStyleSheet("border: 0;")
        self.origo_input.setStyleSheet("border: 0;")
        self.micro_step_1.setStyleSheet("border: 0;")
        self.micro_step_2.setStyleSheet("border: 0;")
        self.micro_step_8.setStyleSheet("border: 0;")
        layout.addSpacing(20)
        layout.addWidget(curve_widget)


    def btnstate(self,b):
        if b.isChecked() == True:
            if b.text() == "Full stepping":
                data["micro_step"] = int(1)	
            elif b.text() == "Micro stepping (1/2)":
                data["micro_step"] = int(2)
            elif b.text() == "Micro stepping (1/8)":
                data["micro_step"] = int(8)
            self.send_serial_message()

    def get_available_ports(self):
        # Retrieve a list of available USB ports
        ports = []
        available_ports = serial.tools.list_ports.comports()
        for port in available_ports:
            # if "USB" in port.description:  # Check if the port description contains "USB"
                ports.append(port.device)
        return ports

    def refresh_ports(self):
        print("refresh_button pushed")
        self.port_combo_box.setCurrentIndex(0)
        self.ports = self.get_available_ports()
        self.ports.insert(0, '-- Select port --')
        self.port_combo_box.clear()
        self.port_combo_box.addItems(self.ports)
        self.connected = False
        self.serial = ""
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.init_button.setEnabled(False)
        self.upload_button.setEnabled(False)
        self.curve_button.setEnabled(False)
        self.loop_count_input.setEnabled(False)
        self.origo_input.setEnabled(False)
        self.micro_step_1.setEnabled(False)
        self.micro_step_2.setEnabled(False)
        self.micro_step_8.setEnabled(False)

    def do_start_button(self):
        print("Start button clicked")
        data["start"] = int(1)
        self.send_serial_message()
        data["start"] = int(0)

    def do_stop_button(self):
        print("Stop button clicked")
        data["stop"] = int(1)
        self.send_serial_message()
        data["stop"] = int(0)

    def do_init_button(self):
        print("init button clicked")
        data["init"] = int(1)
        self.send_serial_message()
        data["init"] = int(0)

    def connect_to_port(self, index):
        print("Connecting to port: " + self.ports[index])
        selected_port = self.ports[index]
        if index == 0:
            print("No port selected")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.init_button.setEnabled(False)
            self.upload_button.setEnabled(False)
            self.curve_button.setEnabled(False)
            self.loop_count_input.setEnabled(False)
            self.origo_input.setEnabled(False)
            self.micro_step_1.setEnabled(False)
            self.micro_step_2.setEnabled(False)
            self.micro_step_8.setEnabled(False)
            self.connected = False
            return

        try:
            self.serial = serial.Serial(selected_port, baudrate=115200)
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.init_button.setEnabled(True)
            self.upload_button.setEnabled(True)
            self.curve_button.setEnabled(True)
            self.loop_count_input.setEnabled(True)
            self.origo_input.setEnabled(True)
            self.micro_step_1.setEnabled(True)
            self.micro_step_2.setEnabled(True)
            self.micro_step_8.setEnabled(True)
            self.connected = True
            self.send_serial_message()
        except serial.SerialException:
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.init_button.setEnabled(False)
            self.upload_button.setEnabled(False)
            self.curve_button.setEnabled(False)
            self.loop_count_input.setEnabled(False)
            self.origo_input.setEnabled(False)
            self.micro_step_1.setEnabled(False)
            self.micro_step_2.setEnabled(False)
            self.micro_step_8.setEnabled(False)
            self.connected = False
            self.port_combo_box.setCurrentIndex(0)
            QMessageBox.warning(self, "Connection Error", "Failed to connect to {}".format(selected_port))

    def send_serial_message(self):
        print(data)
        json_data = json.dumps(data) + '\n'

        try:
            self.serial.write(json_data.encode())
            data["curve"] = []
        except AttributeError:
            QMessageBox.warning(self, "Error", "No port connected. Connect to a port first.")

    def set_loop_count(self):
        data["loop_count"] = int(self.loop_count_input.value())
        self.send_serial_message()

    def set_origo(self):
        data["origo"] = int(self.origo_input.value())
        self.send_serial_message()

    def read_from_file(self):
        file_filter = 'Data File (*.csv)'
        response = QFileDialog.getOpenFileName(
            parent=self,
            caption='Select a file',
            directory=os.getcwd()+"/programs",
            filter=file_filter,
            initialFilter='Data File (*.csv)'
        )
        if response[0] == "":
            return
        selected_file = open(str(response[0])).read()
        file_data = selected_file.splitlines()
        data["freq"] = int(file_data[0])
        print(file_data)
        print(len(file_data))
        file_data.pop(0)
        data["curve_length"] = int(len(file_data))
        data["curve"] = [eval(i) for i in file_data]

    def show_curve_generator(self):
        self.w = CurveGenerator()
        self.w.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = WindowInstance()
    window.show()

    sys.exit(app.exec())