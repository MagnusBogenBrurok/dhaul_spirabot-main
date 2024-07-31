from SpiraBot import SpiraBot, BreathingPattern
from wave_form import*
import time

port_name = "/dev/cu.usbserial-02D9NGJN"

if __name__ == '__main__':

    # Create an instance of SpiraBot and connect to the selected port
    robot = SpiraBot(port=port_name)  # Replace "/dev/ttyUSB0" with the actual port name

    # Connect to port
    while not robot.is_connected():
        print("connecting to spirabot...\n")
        if robot.connect():
            print("Success!")
        else:
            time.sleep(1)

    rpm = 12
    frequency = rpm / 60
    amplitude = 4
    phase = 0
    sampling_rate = 1000
    wave_period = (1 / frequency)
    time_duration = wave_period
    y_step_length = 0.008

    print(time_duration)

    x, y = generate_sine(frequency, amplitude, phase, sampling_rate)
    resampled_x, resampled_y = waveform(x, y, y_step_length)
    time_delay_list, dir_list = calc_time_delays(resampled_x, resampled_y)
    # motor_frq_list = calc_frequencies(time_delay_list)
    motor_frq_list = [2, 3, 4]
    # plot_waveform([resampled_x, x], [resampled_y, y], y_step_length, y_data_third_curve=dir_list)

    # upload custom curve to the SpiraBot
    # robot.upload_curve_from_file("prog.csv")
    # printing the data that was sent
    print(motor_frq_list)
    robot.upload_curve(curve=motor_frq_list, sampling_freq=sampling_rate, send_data=True)
    #
    time.sleep(4)
    print("data", robot.get_data())
    #

    # Start playing the uploaded curve
    robot.start(loop_count=1)

    i = input()
    robot.stop()







