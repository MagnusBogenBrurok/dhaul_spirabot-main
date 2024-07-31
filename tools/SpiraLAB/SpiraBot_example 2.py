from SpiraBot import SpiraBot, BreathingPattern
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

    wave = BreathingPattern(sample_frq=10, rpm=10, duration_s=30, amplitude_max_mm=2)
    wave_2 = BreathingPattern(17, 15, int(60/15), 2)
    wave_3 = BreathingPattern(17, 20, int(60 / 20), 2)
    wave_4 = BreathingPattern(17, 25, int(60/25), 2)

    wave_2_data = wave_2.sine_wave()
    wave_3_data = wave_3.sine_wave()
    wave_4_data = wave_4.sine_wave()
    wave_data = wave.sine_wave()
    wave.print_wave()

    # upload custom curve to the SpiraBot
    # robot.upload_curve_from_file("prog.csv")
    # printing the data that was sent
    robot.upload_curve(curve=wave_data, sampling_freq=10, send_data=True)
    #
    time.sleep(4)
    print("data", robot.get_data())
    #

    # Start playing the uploaded curve
    robot.start(loop_count=1)
    time.sleep(60)
    robot.stop()







