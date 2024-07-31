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


def round_up_to_factor(number, factor):
    return math.ceil(number / factor) * factor


def round_down_to_factor(number, factor):
    return math.floor(number / factor) * factor


def waveform(x_data, y_data, step_length):
    """
    This function takes in the x and y data and returns the waveform resampled at the step length along the y axis.
    Every point on the curve has a y-value that is a factor of the step_length, and then generates the corresponding
    x-values by interpolation.
    """

    resampled_x = []
    resampled_y = []

    for y in range(0, len(y_data) - 1):
        if y > len(x_data):
            break
        delta = (y_data[y + 1] - y_data[y])
        if delta:
            dir_sign = (y_data[y + 1] - y_data[y]) / abs((y_data[y + 1] - y_data[y]))
        else:
            dir_sign = 1
        sub_y_data = [y_data[y], y_data[y + 1]]
        sub_x_data = [x_data[y], x_data[y + 1]]

        if resampled_y:
            if dir_sign > 0:
                min_y = min(sub_y_data)
                max_y = max(sub_y_data)
                min_y = round_up_to_factor(min_y, step_length)
                sub_y_axis = np.arange(min_y, max_y, step_length)
                sub_x_axis = np.interp(sub_y_axis, sub_y_data, sub_x_data)
                resampled_x.extend(sub_x_axis)
                resampled_y.extend(sub_y_axis)

            # If dir_sign is negative we need to mirror the function about y = 0 before the resampling, and
            # mirror it back again afterwards.
            else:
                sub_y_data[0] = -1*sub_y_data[0]
                sub_y_data[1] = -1*sub_y_data[1]
                min_y = min(sub_y_data)
                max_y = max(sub_y_data)
                min_y = round_up_to_factor(min_y, step_length)
                sub_y_axis = np.arange(min_y, max_y, step_length)
                sub_x_axis = np.interp(sub_y_axis, sub_y_data, sub_x_data)
                for i in range(0, len(sub_y_axis)):
                    sub_y_axis[i] *= -1
                resampled_x.extend(sub_x_axis)
                resampled_y.extend(sub_y_axis)

        else:
            min_y = min(sub_y_data)
            max_y = max(sub_y_data)
            sub_y_axis = np.arange(min_y, max_y, step_length)
            sub_x_axis = np.interp(sub_y_axis, sub_y_data, sub_x_data)
            resampled_x.extend(sub_x_axis)
            resampled_y.extend(sub_y_axis)

    return resampled_x, resampled_y


def calc_time_delays(time_data, amp_data):
    time_delays = []
    directions = []
    if len(time_data) != len(amp_data):
        print("Error: time_data and amp_data needs to be the same length..")
        return [], []
    for t in range(1, len(time_data)):
        current_time_delay = time_data[t] - time_data[t - 1]
        current_direction = (amp_data[t] - amp_data[t - 1]) / abs((amp_data[t] - amp_data[t - 1]))
        time_delays.append(current_time_delay)
        directions.append(int(current_direction))

    return time_delays, directions


def calc_frequencies(delay_data):
    frequencies = []
    for t in delay_data:
        freq = int(1 / t)
        frequencies.append(freq)

    return frequencies


def generate_sine(frequency, amplitude, phase, sampling_rate, time=0):
    """
    This function generates a sine wave given the frequency, amplitude, phase, and time.
    """

    if not time:
        # time is not given. Defaults to 1 periode of the sine wave
        time = 1 / frequency

    # Create the x axis
    x = np.arange(0, time, 1 / sampling_rate)

    # Create the y axis
    y = amplitude * np.sin(2 * np.pi * frequency * x + phase)

    return x, y


def plot_waveform(x_data_list, y_data_list, step_length, show_grid=False, y_data_third_curve=None):
    """
    This function takes in multiple sets of x and y data and plots the waveforms and plots each sample point as a red dot.
    It also adds grid lines at the y-axis for the specified step_length.
    """

    # Create a new figure and subplots
    fig, (ax1, ax2) = plt.subplots(2, 1)

    # Plot the waveforms in the first subplot (ax1)
    for x_data, y_data in zip(x_data_list, y_data_list):
        ax1.plot(x_data, y_data)

    # Plot the sample points for the first waveform in the first subplot (ax1)
    ax1.plot(x_data_list[0], y_data_list[0], 'ro', color='b')
    ax1.set_ylabel('Amplitude (mm)')

    # Calculate the y-axis grid line positions based on step_length
    if show_grid:
        min_y = min(min(y_data) for y_data in y_data_list)
        min_y = round_down_to_factor(min_y, step_length)
        max_y = max(max(y_data) for y_data in y_data_list)
        max_y = round_up_to_factor(max_y, step_length)
        y_ticks = [round(y, 1) for y in plt.yticks()[0] if min_y <= y <= max_y]
        grid_line_positions = np.arange(min_y, max_y, step_length)
        grid_line_positions = list(grid_line_positions)

        # Filter grid line positions to avoid duplicate ticks
        y_ticks = [tick for tick in y_ticks if tick not in grid_line_positions]

        # Combine the original y_ticks with the grid_line_positions
        y_ticks += grid_line_positions

        ax1.set_yticks(y_ticks)

    # Show the grid lines in the first subplot (ax1)
    ax1.grid(axis='y', linestyle='--', alpha=0.7)

    # Create the third subplot for the third curve with shared x-axis
    if y_data_third_curve is not None:
        ax2_x_values = x_data_list[0][1:]
        ax2 = fig.add_subplot(212, sharex=ax1)
        dot_color = 'black'
        ax2.plot(ax2_x_values, y_data_third_curve, 'ro', color='r')
        # ax2.plot(ax2_x_values, y_data_third_curve)
        # ax2.plot(ax2_x_values, y_data_third_curve, 'ro')
        ax2.set_ylabel('Y-axis (Motor direction)')
        # ax2.grid(axis='y', linestyle='--', alpha=1)

        # Set y-axis ticks and labels for the second subplot (ax2)
        # ax2.set_yticks([-1, 1], minor=True)
        # ax2.set_yticklabels(['In', 'Out'])

    # Show the plot
    # plt.tight_layout()
    plt.show()


class BreathingPattern:
    def __init__(self, sample_frq=1000, rpm, duration_s, amplitude_max_mm):
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
