import json
import serial
import math
import numpy as np
import matplotlib.pyplot as plt


def time_axis(length_s, sample_freq_hz):
    time = []
    for t in np.arange(0, length_s + (1 / sample_freq_hz), (1 / sample_freq_hz)):
        time.append(round(t, 2))
    return time


class BreathingPattern:
    def __init__(self, sample_frq, rpm, duration_s, amplitude_max_mm):
        self._amplitude_mm = amplitude_max_mm
        self.sample_freq = sample_frq
        self._rpm = rpm
        self.duration_s = duration_s
        self._robot_step_length = 0.01
        self._wave_amplitudes = []

        self._time = []
        self._step_count = []
        self._inverse_wave = []

    def _generate_wave_sine(self):
        self._time = time_axis(self.duration_s, self.sample_freq)
        for t in self._time:
            self._wave_amplitudes.append(self._amplitude_mm * np.sin(2 * np.pi * t / (60 / self._rpm)))
        self._wave_amplitudes[-1] = 0.0

    def sine_wave(self):
        self._generate_wave_sine()
        self._generate_output_wave()
        return self._step_count

    def _generate_output_wave(self):
        # Count the number of steps between each time step
        self._step_count = []
        prev_input_wave = 0
        i = 0
        step_overflow = 0
        for t in self._time:
            steps = 1/self._robot_step_length * (self._wave_amplitudes[i] - prev_input_wave)
            if steps > 0:
                step_overflow += steps - math.floor(steps)
                if step_overflow >= 1:
                    self._step_count.append(math.floor(steps) + 1)
                    step_overflow -= 1
                else:
                    self._step_count.append(math.floor(steps))
            else:
                step_overflow += steps + math.floor(abs(steps))
                if step_overflow <= -1:
                    self._step_count.append(-math.floor(abs(steps)) - 1)
                    step_overflow += 1
                else:
                    self._step_count.append(-math.floor(abs(steps)))
            prev_input_wave = self._wave_amplitudes[i]
            i += 1

        # Compensate for rounding errors
        res = 0
        for i in range(len(self._step_count)):
            res += self._step_count[i]
        if res != 0:
            self._step_count[len(self._step_count) - 1] -= res

        max_steps = 1200 / self.sample_freq
        overflow = 0
        for i in range(len(self._step_count)):
            if self._step_count[i] + overflow > max_steps:
                overflow += self._step_count[i] - max_steps
                self._step_count[i] = max_steps
            elif self._step_count[i] + overflow < -max_steps:
                overflow += self._step_count[i] + max_steps
                self._step_count[i] = -max_steps
            else:
                self._step_count[i] += overflow
                overflow = 0

        # Generate output wave from step count
        self._inverse_wave = []
        prev_output_wave = 0
        for i in range(len(self._step_count)):
            self._inverse_wave.append((self._step_count[i] / (1/self._robot_step_length)) + prev_output_wave)
            prev_output_wave = self._inverse_wave[i]

    def print_wave(self):
        # Plot the breathing pattern curve
        plt.figure(figsize=(10, 6))
        plt.plot(self._time, self._wave_amplitudes, label='Breathing Pattern')
        plt.xlabel('Time (s)')
        plt.ylabel('Amplitude (mm)')
        plt.title('Realistic Breathing Pattern')
        plt.legend()
        plt.grid(True)
        plt.show()


class SpiraBot:
    def __init__(self, port, baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self._serial = None
        self._connected = False
        self._data = {
            "start": 0,
            "init": 0,
            "stop": 0,
            "loop_count": -1,
            "origo": 11,
            "micro_step": 8,
            "freq": 17,
            "curve_length": 0,
            "curve": [],
        }

    # ############ Set functions ##############
    def start(self, loop_count=-1):
        self.set_loop_count(loop_count=loop_count)
        self.set_flag(flag="start", value=1)
        self.set_flag(flag="stop", value=0)
        self.send_data(["start", "stop", "loop_count"])

    def stop(self):
        self.set_flag(flag="start", value=0)
        self.set_flag(flag="stop", value=1)
        self.send_data(["start", "stop"])

    def set_flag(self, flag, value, send_data=False):
        try:
            if value:
                self._data[flag] = 1
            else:
                self._data[flag] = 0

            if send_data:
                self.send_data([flag])
        except KeyError:
            return 0
        return 1

    def set_loop_count(self, loop_count, send_data=False):
        self._data["loop_count"] = loop_count
        if send_data:
            self.send_data(["loop_count"])

    def set_origo(self, origo, send_data=False):
        self._data["origo"] = origo
        if send_data:
            self.send_data(["origo"])

    def set_micro_steps(self, micro_step, send_data=False):
        self._data["micro_step"] = micro_step
        if send_data:
            self.send_data("micro_step")

    def set_freq(self, freq, send_data=False):
        self._data["freq"] = freq
        if send_data:
            self.send_data(["freq"])

    # #########################################
    def connect(self):
        try:
            self._serial = serial.Serial(self.port, baudrate=self.baudrate)
            self._connected = True
        except serial.SerialException:
            self._connected = False

        return self._connected

    def is_connected(self):
        return self._connected

    def disconnect(self):
        if self.serial:
            self.serial.close()
            self.connected = False

    def send_all_data(self):
        if not self._connected:
            raise ConnectionError("Not connected to the robot. Connect first using connect() method.")

        json_data = json.dumps(self._data) + '\n'
        self._serial.write(json_data.encode())

    def send_data(self, data_attributes):
        if not self._connected:
            raise ConnectionError("Not connected to the robot. Connect first using connect() method.")

        temp_data = {}
        for attribute in data_attributes:
            if attribute in self._data:
                temp_data[attribute] = self._data[attribute]
        print(temp_data)
        json_data = json.dumps(temp_data) + '\n'
        self._serial.write(json_data.encode())

    def upload_curve(self, curve, sampling_freq, send_data=False):
        self._data["curve_length"] = len(curve)
        self._data["curve"] = curve
        self._data["freq"] = sampling_freq
        if send_data:
            self.set_flag("start", 1)
            self.set_flag("stop", 0)
            self.send_all_data()

    def upload_curve_from_file(self, filename):
        variables = {}
        data = []
        with open(filename, 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith('#'):
                    parts = line.split('=')
                    if len(parts) == 2:
                        var_name = parts[0][1:]  # Removing the leading '#'
                        print(var_name)
                        var_value = int(parts[1].strip())
                        print(var_value)
                        variables[var_name] = var_value
                else:
                    data.append(int(line))
        for var in variables:
            if var in self._data:
                self._data[var] = variables[var]
        self.upload_curve(data)

    def get_data(self):
        return self._data
