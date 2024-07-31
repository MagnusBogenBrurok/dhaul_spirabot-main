#include <stdint.h>

#ifndef WAVEFORM
#define WAVEFORM

#define DEFAULT_SAMPLE_RATE 200
#define DEFAULT_SINE_WAVE_PHASE 0
#define DEFAULT_SINE_WAVE_AMPLITUDE 3
#define DEFAULT_SINE_WAVE_RPM 30
#define DEFAULT_SINE_WAVE_TIME_DURATION -1
#define DEFAULT_CURVE_TYPE COS

typedef struct
{
    float rpm;       // RPM of the sine wave
    float amplitude; // amplitude of the sine wave
    float phase;     // Phase shift
    int sample_rate;
    float time_duration;
    int curve_type;
} waveform_sine_encoder_config_t;

typedef struct
{
    float *t_values; // Time
    float *y_values; // Amplitude
    int number_of_samples;
} waveform_sine_wave_t;

typedef struct
{
    int *step_freq;      // The frequency (1/time duration) for each step in the curve
    int number_of_steps; // Number of steps in the curve
} waveform_step_frequency_t;

typedef enum
{
    COS = 1,
    DOUBLE_COS = 2,
} curve_type_t;

void generate_sine(waveform_sine_encoder_config_t *config, waveform_sine_wave_t *sine_wave);
void generate_cosine(waveform_sine_encoder_config_t *config, waveform_sine_wave_t *cosine_wave);
void generate_breathing_pattern_1(waveform_sine_encoder_config_t *config, waveform_sine_wave_t *cosine_wave);
float interp(float x0, float y0, float x1, float y1, float yp);
void waveform_resamp(float *x, float *y, float *x_new, float *y_new, int size, int new_size);
void waveform_convert_to_steps(waveform_sine_wave_t *sine_wave_resamp, waveform_step_frequency_t *step_freq, int size);

#endif