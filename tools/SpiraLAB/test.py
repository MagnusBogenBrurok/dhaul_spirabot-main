import math
import matplotlib.pyplot as plt

def generate_breathing_curve(max_amplitude, breathing_freq, sampling_freq, duration):
    num_samples = int(sampling_freq * 60)
    time = [i / sampling_freq for i in range(num_samples)]
    breathing_curve = []

    # Components of the breathing pattern
    inhale_freq = 0.25  # Low frequency component for inhalation
    inhale_amplitude = max_amplitude * 0.7  # Amplitude for inhalation
    inhale_phase = 0  # Phase shift for inhalation (radians)

    exhale_freq = 0.35  # Low frequency component for exhalation
    exhale_amplitude = max_amplitude * 0.9  # Amplitude for exhalation
    exhale_phase = math.pi  # Phase shift for exhalation (radians)

    # Additional components for variation
    inhale_high_freq = 3.5  # High frequency component for inhalation
    inhale_high_amplitude = max_amplitude * 0.1  # Amplitude for high-frequency inhalation
    inhale_high_phase = 0  # Phase shift for high-frequency inhalation (radians)

    exhale_high_freq = 4.5  # High frequency component for exhalation
    exhale_high_amplitude = max_amplitude * 0.1  # Amplitude for high-frequency exhalation
    exhale_high_phase = 0  # Phase shift for high-frequency exhalation (radians)

    # Generate the breathing pattern curve using a sum of sinusoids
    for t in time:
        inhale_component = inhale_amplitude * math.sin(2 * math.pi * inhale_freq * t + inhale_phase)
        exhale_component = exhale_amplitude * math.sin(2 * math.pi * exhale_freq * t + exhale_phase)

        inhale_high_component = inhale_high_amplitude * math.sin(2 * math.pi * inhale_high_freq * t + inhale_high_phase)
        exhale_high_component = exhale_high_amplitude * math.sin(2 * math.pi * exhale_high_freq * t + exhale_high_phase)

        amplitude = inhale_component + exhale_component + inhale_high_component + exhale_high_component
        breathing_curve.append(amplitude)

    breathing_curve = breathing_curve[:duration * sampling_freq]
    return breathing_curve

# Parameters
max_amplitude = 2  # mm
breathing_freq = 12  # breaths per minute
sampling_freq = 17  # Hz
duration = 60  # seconds

# Generate the breathing pattern curve
breathing_curve = generate_breathing_curve(max_amplitude, breathing_freq / 60, sampling_freq, duration)
breathing_curve = breathing_curve[:10*sampling_freq]
# Time vector for plotting
num_samples = int(sampling_freq * 10)
time = [i / sampling_freq for i in range(num_samples)]

# Plot the breathing pattern curve
plt.figure(figsize=(10, 6))
plt.plot(time, breathing_curve, label='Breathing Curve')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude (mm)')
plt.title('Realistic Breathing Curve')
plt.legend()
plt.grid(True)
plt.show()
