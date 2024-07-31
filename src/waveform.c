#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include "waveform.h"
#include "esp_log.h"

static const char *TAG = "WAVEFORM";

void generate_sine(waveform_sine_encoder_config_t *config, waveform_sine_wave_t *sine_wave)
{
    ESP_LOGI(TAG, "Generate sine");
    float frequency = config->rpm / 60;
    float time = config->time_duration;
    if (time == -1)
    {
        time = 1 / frequency;
    };

    for (int i = 0; i < sine_wave->number_of_samples; i++)
    {
        sine_wave->t_values[i] = (float)i / config->sample_rate;
        sine_wave->y_values[i] = config->amplitude * sin(2 * M_PI * frequency * sine_wave->t_values[i] + config->phase);
    }
}

void generate_cosine(waveform_sine_encoder_config_t *config, waveform_sine_wave_t *cosine_wave)
{
    ESP_LOGI(TAG, "Generate cosine");
    float frequency = config->rpm / 60;

    for (int i = 0; i < cosine_wave->number_of_samples - 1; i++)
    {
        cosine_wave->t_values[i] = (float)i / config->sample_rate;
        cosine_wave->y_values[i] = config->amplitude + (config->amplitude * cos(2 * M_PI * frequency * ((float)(i + (cosine_wave->number_of_samples - 1)) / config->sample_rate) + config->phase));
    }
    cosine_wave->t_values[cosine_wave->number_of_samples - 1] = config->time_duration;
    cosine_wave->y_values[0] = 0;
    cosine_wave->y_values[cosine_wave->number_of_samples - 1] = config->amplitude * 2;
}

void generate_breathing_pattern_1(waveform_sine_encoder_config_t *config, waveform_sine_wave_t *cosine_wave)
{
    ESP_LOGI(TAG, "Generate breathing pattern 1");
    float frequency = config->rpm / 60;
    float amplitude = config->amplitude / 2;
    float time_duration = config->time_duration / 2;
    int number_of_samples = cosine_wave->number_of_samples / 2;
    float sample_rate = config->sample_rate / 2;

    for (int i = 0; i < number_of_samples - 1; i++)
    {
        cosine_wave->t_values[i] = (float)i / config->sample_rate;
        cosine_wave->y_values[i] = amplitude + (amplitude * cos(2 * M_PI * frequency * (float)(i + (number_of_samples - 1)) / sample_rate));
    }
    cosine_wave->t_values[number_of_samples - 1] = time_duration;
    cosine_wave->y_values[0] = 0;
    cosine_wave->y_values[number_of_samples - 1] = amplitude * 2;

    for (int i = number_of_samples; i < cosine_wave->number_of_samples - 1; i++)
    {
        cosine_wave->t_values[i] = (float)i / config->sample_rate;
        cosine_wave->y_values[i] = (3 * amplitude) + (amplitude * cos(2 * M_PI * frequency * (float)(i - 1) / sample_rate));
    }
    cosine_wave->t_values[cosine_wave->number_of_samples - 1] = config->time_duration;
    cosine_wave->y_values[number_of_samples] = config->amplitude;
    cosine_wave->y_values[cosine_wave->number_of_samples - 1] = config->amplitude * 2;
}

float interp(float x0, float y0, float x1, float y1, float yp)
{
    return ((x0 * (y1 - yp)) + (x1 * (yp - y0))) / (y1 - y0);
}

void waveform_resamp(float *x, float *y, float *x_new, float *y_new, int size, int new_size)
{
    for (int i = 0; i < new_size - 1; i++)
    {
        for (int j = 0; j < size; j++)
        {
            if (y_new[i] < y[j])
            {
                int idx = j - 1;
                float x_0 = x[idx];
                float x_1 = x[idx + 1];
                float y_0 = y[idx];
                float y_1 = y[idx + 1];
                x_new[i] = interp(x_0, y_0, x_1, y_1, y_new[i]);
                break;
            }
        }
    }
    x_new[new_size - 1] = x[size - 1];
}

void waveform_convert_to_steps(waveform_sine_wave_t *sine_wave_resamp, waveform_step_frequency_t *step_freq, int size)
{
    ESP_LOGI(TAG, "Convert_to_steps");
    float current_time, next_time, delta_time;
    for (int i = 0; i < size; i++)
    {
        current_time = sine_wave_resamp->t_values[i];
        next_time = sine_wave_resamp->t_values[i + 1];
        delta_time = next_time - current_time;
        if (delta_time < 0)
        {
            ESP_LOGI(TAG, "Delta time (%d/%d) cannot have negative value:  %f", i, size - 1, delta_time);
        }
        step_freq->step_freq[i] = (int)round(1.0 / delta_time);
    }
}