

def find_f_from_sum(S, a):
    # Calculate the sum part of the formula
    sum_part = S * 2 / (a / 0.15)
    
    # Calculate the value of f
    f = (sum_part - 0.05 - 0.05 * (a / 0.15)) / (2 / (a / 0.15))
    
    return f


def calculate_time(start_freq, amplitude, acc_increment):
    steps = amplitude*100
    constant_steps = int((1/3)*steps)
    print(f"Constant steps: {constant_steps}")
    # First calculate the constant frequenzy
    f_constant = start_freq + (constant_steps*acc_increment)
    # average frequenzy for acc-phase
    f_acc_avg = (f_constant - start_freq)/2 + start_freq


    # calculate time spent in the constant phase
    t_constant = (2/f_constant)*constant_steps
    print(f"Constant time: {t_constant}")

    t_acc = (2/f_acc_avg)*constant_steps
    print(f"Acc time: {t_acc}")

    total_t = (t_constant + 2*t_acc)

    rpm = (60/total_t)

    return total_t, rpm



def start_frequency(rpm, amplitude, acc_increment):
    rpm_num = 0
    start_freq = 0
    while True:
        time, rpm_aprox = calculate_time(start_freq, amplitude, acc_increment)
        if rpm_aprox > rpm:
            return start_freq
        start_freq += 1



# Example usage
s = 27 
a = 2 
a_i = 3


t, rpm = calculate_time(s, a, a_i)
print(f"The value of t is: {t}")
print(f"The rpm is: {rpm}")

#s_f = start_frequency(12, )