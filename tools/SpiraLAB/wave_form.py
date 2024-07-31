import numpy as np
import matplotlib.pyplot as plt
import math


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



def test():
    rpm = 20
    frequency = rpm / 60
    amplitude = 4
    phase = 0
    sampling_rate = 100
    wave_period = (1 / frequency)
    time_duration = wave_period
    y_step_length = 0.008

    print(time_duration)

    x, y = generate_sine(frequency, amplitude, phase, sampling_rate)
    resampled_x, resampled_y = waveform(x, y, y_step_length)
    time_delay_list, dir_list = calc_time_delays(resampled_x, resampled_y)
    motor_frequency_list = calc_frequencies(time_delay_list)
    print(motor_frequency_list)
    print("length: ", len(motor_frequency_list))

    plot_waveform([resampled_x, x], [resampled_y, y], y_step_length)

    plot_waveform([resampled_x[:-1], x], [motor_frequency_list, y], y_step_length)



def test2():
    rpm = 13
    frequency = rpm / 60
    amplitude = 4
    phase = 0
    sampling_rate = 1000
    y_step_length = 0.008
    wave_period = 1 / frequency

    x, y = generate_sine(frequency, amplitude, phase, sampling_rate, wave_period)
    # Scale the x_values so that the period corresponds to 2*pi
    # x = x * 2 * np.pi / wave_period
    # print(x)
    resampled_x, resampled_y = waveform2(x, y, y_step_length, 2*np.pi*wave_period)

    plot_waveform([resampled_x, x], [resampled_y, y], y_step_length)


if __name__ == "__main__":
    test()
