#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_timer.h"
#include "esp_log.h"
#include "uart.h"
#include "state_machine.h"
#include "robot.h"
#include "waveform.h"
#include "freertos/semphr.h"
#include "nvs_flash.h"
#include "nvs.h"
#include <stdlib.h>
#include "math.h"
#include "string.h"

static const char *TAG = "STATE_MACHINE";
const char *error_message = "Error";

curve_mode_t curve_mode;
robot_config_t robot_config;
robot_state_t current_state;
action_flag_t action_flags;

waveform_sine_encoder_config_t sine_encoder_config;

float sine_wave_t_val[MAX_SINE_WAVE_VAL_LENGTH];
float sine_wave_y_val[MAX_SINE_WAVE_VAL_LENGTH];
float sine_wave_resamp_t_val[MAX_SINE_WAVE_RESAMP_LENGTH];
float sine_wave_resamp_y_val[MAX_SINE_WAVE_RESAMP_LENGTH];
int sine_wave_freq_list[MAX_SINE_WAVE_FREQ_LIST_LENGTH];

char serial_number[15]; // Adjust size as necessary

void init_action_flags(void)
{
    action_flags.init_flag = DEFAULT_INIT_FLAG;
    action_flags.stop_flag = DEFAULT_STOP_FLAG;
    action_flags.update_flag = DEFAULT_UPDATE_FLAG;
}

void init_robot_config(void)
{
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND)
    {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    robot_config.current_dir = DIR_STOP;
    robot_config.current_pos = 0;
    robot_config.error = 0;
    robot_config.microstep = DEFAULT_MICRO_STEP;
    robot_config.origo = 0;
    robot_config.step_length = 1.0 / robot_config.microstep;
    for (int i = 0; i < SLOT_MAP_SIZE; i++)
    {
        robot_config.slot_map[i] = 0;
    }

    int32_t last_sine_amplitude = read_value("last_sine_amp");
    int32_t last_sine_rpm = read_value("last_sine_rpm");
    int32_t last_curve_type = read_value("last_curve_type");
    int32_t amnesia = read_value("amnesia");

    if (!last_sine_rpm || !last_sine_amplitude || !last_curve_type)
    {
        sine_encoder_config.amplitude = DEFAULT_SINE_WAVE_AMPLITUDE;
        sine_encoder_config.rpm = DEFAULT_SINE_WAVE_RPM;
        sine_encoder_config.curve_type = DEFAULT_CURVE_TYPE;
        action_flags.stop_flag = 1;
    }

    else if (amnesia)
    {
        sine_encoder_config.amplitude = DEFAULT_SINE_WAVE_AMPLITUDE;
        sine_encoder_config.rpm = DEFAULT_SINE_WAVE_RPM;
        sine_encoder_config.curve_type = DEFAULT_CURVE_TYPE;
        action_flags.stop_flag = 1;
    }

    else
    {
        sine_encoder_config.amplitude = last_sine_amplitude;
        sine_encoder_config.rpm = last_sine_rpm;
        sine_encoder_config.curve_type = last_curve_type;
        action_flags.stop_flag = 0;
    }

    sine_encoder_config.phase = DEFAULT_SINE_WAVE_PHASE;
    sine_encoder_config.sample_rate = DEFAULT_SAMPLE_RATE;
    sine_encoder_config.time_duration = DEFAULT_SINE_WAVE_TIME_DURATION;
}

void state_machine_loop(void *pvParameters)
{
    ESP_LOGI(TAG, "Initialize robot hardware");
    current_state = STATE_INIT;
    curve_mode = DEFAULT_CURVE_MODE;
    while (1)
    {
        switch (current_state)
        {
        case STATE_INIT:
            current_state = state_machine_do_init();
            break;

        case STATE_IDLE:
            current_state = state_machine_do_idle();
            break;

        case STATE_SINE_WAVE:
            current_state = state_machine_do_sine_wave();
            break;

        case STATE_ERROR:
            current_state = state_machine_do_error();
            break;

        case STATE_MOVE_ORIGO:
            current_state = state_machine_do_move_origo();
            break;

        default:
            break;
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

robot_state_t state_machine_do_error(void)
{
    // Error handling
    action_flags.stop_flag = 1;
    action_flags.update_flag = 0;
    return STATE_IDLE;
}

robot_state_t state_machine_do_init(void)
{
    init_action_flags();
    init_robot_config();
    
    curve_mode = SINE_WAVE;

    if (!robot_init(&robot_config))
    {
        ESP_LOGI(TAG, "Unable to initialize robot hardware");
    }

    /*get_serial_number(robot_config.serial_number, sizeof(robot_config.serial_number));
    // Check if serial number is set
    if (strncmp(robot_config.serial_number, "AB1G", 4) == 0){
        get_serial_number(robot_config.serial_number, sizeof(robot_config.serial_number));
    }
    else{
        save_serial_number(DEFAULT_SERIAL_NUMBER);
        get_serial_number(robot_config.serial_number, sizeof(robot_config.serial_number));
    }
    
    //printf(robot_config.serial_number);
    */
    robot_motor_init(&robot_config);

    return STATE_IDLE;
}

robot_state_t state_machine_do_idle(void)
{
    ESP_LOGI(TAG, "Idle");
    robot_motor_set_dir(DIR_STOP, &robot_config);
    while (1)
    {
        float origo_error = (robot_config.origo - robot_config.current_pos);
        if (origo_error < 0)
        {
            origo_error = -1.0 * origo_error;
        }

        if (origo_error > robot_config.step_length)
        {
            ESP_LOGI(TAG, "Error: %f", origo_error);
            return STATE_MOVE_ORIGO;
        }

        if (action_flags.update_flag)
        {
            action_flags.update_flag = 0;
            action_flags.stop_flag = 0;
            return STATE_SINE_WAVE;
        }

        if (!action_flags.stop_flag)
        {
            return STATE_SINE_WAVE;
        }

        if (action_flags.init_flag)
        {
            action_flags.init_flag = 0;
            return STATE_INIT;
        }
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}

robot_state_t state_machine_do_move_origo(void)
{
    robot_motor_go_to_abs_pos_mm(robot_config.origo, 20, &robot_config);
    return STATE_IDLE;
}

robot_state_t state_machine_do_sine_wave(void)
{

    if (parameter_validtion_check(sine_encoder_config.amplitude, sine_encoder_config.rpm, robot_config.microstep) == 0)
    {
        ESP_LOGE(TAG, "Invalid parameters");
        return STATE_ERROR;
    }
    save_value("last_sine_amp", sine_encoder_config.amplitude);
    save_value("last_sine_rpm", sine_encoder_config.rpm);
    save_value("last_curve_type", sine_encoder_config.curve_type);

    if (robot_config.origo != robot_config.current_pos)
    {

        robot_motor_go_to_abs_pos_mm(robot_config.origo, 50, &robot_config);
    }

    if (sine_encoder_config.time_duration == -1)
    {
        sine_encoder_config.time_duration = 1 / (sine_encoder_config.rpm / 30);
    }

    int sine_wave_val_length = (sine_encoder_config.time_duration * sine_encoder_config.sample_rate) + 1;
    waveform_sine_wave_t sine_wave = {
        .number_of_samples = sine_wave_val_length,
        .t_values = sine_wave_t_val,
        .y_values = sine_wave_y_val,
    };

    int sine_wave_resamp_length = (int)(2 * sine_encoder_config.amplitude / robot_config.step_length + 1);
    waveform_sine_wave_t sine_wave_resamp = {
        .number_of_samples = sine_wave_resamp_length,
        .t_values = sine_wave_resamp_t_val,
        .y_values = sine_wave_resamp_y_val,
    };

    waveform_step_frequency_t sine_wave_step_freq = {
        .number_of_steps = sine_wave_resamp_length,
        .step_freq = sine_wave_freq_list,
    };

    sine_wave_resamp.y_values[0] = 0;
    for (int i = 1; i < sine_wave_resamp_length; i++)
    {
        sine_wave_resamp.y_values[i] = sine_wave_resamp.y_values[i - 1] + robot_config.step_length;
    }

    switch (sine_encoder_config.curve_type)
    {
    case DOUBLE_COS:
        generate_breathing_pattern_1(&sine_encoder_config, &sine_wave);
        break;

    default:
        generate_cosine(&sine_encoder_config, &sine_wave);
        break;
    }

    waveform_resamp(sine_wave.t_values, sine_wave.y_values, sine_wave_resamp.t_values, sine_wave_resamp.y_values, sine_wave.number_of_samples, sine_wave_resamp.number_of_samples);
    waveform_convert_to_steps(&sine_wave_resamp, &sine_wave_step_freq, sine_wave_resamp.number_of_samples);
    robot_motor_do_curve(&action_flags.stop_flag, sine_wave_step_freq.step_freq, sine_wave_step_freq.number_of_steps - 1, &robot_config);

    if (robot_config.error)
    {
        robot_config.error = 0;
        return STATE_INIT;
    }

    return STATE_IDLE;
}

void save_value(const char *key, int32_t value)
{
    nvs_handle_t my_handle;
    esp_err_t err;

    // Open NVS namespace "storage" for writing
    err = nvs_open("storage", NVS_READWRITE, &my_handle);
    if (err != ESP_OK)
    {
        // printf("Error (%s) opening NVS handle!\n", esp_err_to_name(err));
        return;
    }

    // Write value to NVS
    err = nvs_set_i32(my_handle, key, value);
    if (err != ESP_OK)
    {
        // printf("Error (%s) writing value to NVS!\n", esp_err_to_name(err));
        return;
    }

    // Commit the value to NVS
    err = nvs_commit(my_handle);
    if (err != ESP_OK)
    {
        // printf("Error (%s) committing value to NVS!\n", esp_err_to_name(err));
        return;
    }

    // Close the NVS handle
    nvs_close(my_handle);
}

int32_t read_value(const char *key)
{
    nvs_handle_t my_handle;
    int32_t value = 0; // default value if key doesn't exist
    esp_err_t err;

    // Open NVS namespace "storage" for reading
    err = nvs_open("storage", NVS_READONLY, &my_handle);
    if (err != ESP_OK)
    {
        // printf("Error (%s) opening NVS handle!\n", esp_err_to_name(err));
        return value;
    }

    // Read value from NVS
    err = nvs_get_i32(my_handle, key, &value);
    switch (err)
    {
    case ESP_OK:
        // printf("Read value from NVS: %ld\n", value);
        break;
    case ESP_ERR_NVS_NOT_FOUND:
        // printf("Key not found in NVS!\n");
        break;
    default:
        // printf("Error (%s) reading value from NVS!\n", esp_err_to_name(err));
    }

    // Close the NVS handle
    nvs_close(my_handle);

    return value;
}

void save_serial_number(const char* serial_number){
    // Initialize NVS
    esp_err_t err;
    // Open
    nvs_handle_t my_handle;
    err = nvs_open(STORAGE_NAMESPACE, NVS_READWRITE, &my_handle);
    if (err == ESP_OK) {
        // Write
        err = nvs_set_str(my_handle, "serial_number", serial_number);
        // Commit
        err = nvs_commit(my_handle);
        // Close
        nvs_close(my_handle);
    }
}

void get_serial_number(char* serial_number, size_t max_len){

    // Open
    nvs_handle_t my_handle;
    esp_err_t err;
    err = nvs_open(STORAGE_NAMESPACE, NVS_READONLY, &my_handle);
    if (err == ESP_OK) {
        // Read
        err = nvs_get_str(my_handle, "serial_number", serial_number, &max_len);
        // Close
        nvs_close(my_handle);
    }
}

int parameter_validtion_check(float amplitude, float rpm, int microstep){
    int valid = 1;
    if ((amplitude <= 0) || (rpm <= 0)){
        ESP_LOGE(TAG, "Invalid amplitude or rpm value");
        send_error_message("Invalid amplitude or rpm value");
        valid = 0;
    }
    if ((microstep != 1) && (microstep != 2) && (microstep != 8)){
        ESP_LOGE(TAG, "Invalid microstep value");
        send_error_message("Invalid microstep value");
        valid = 0;
    }
    if (microstep*amplitude > 24){
        ESP_LOGE(TAG, "Invalid microstep and amplitude combination");
        send_error_message("Invalid microstep and amplitude combination");
        valid = 0;
    }
    
    if (rpm > 30 && amplitude > 2){
        ESP_LOGE(TAG, "Invalid rpm and amplitude combination");
        send_error_message("Invalid rpm and amplitude combination");
        valid = 0;
    }

    else if (rpm > 60 && amplitude > 1){
        ESP_LOGE(TAG, "Invalid rpm and amplitude combination");
        send_error_message("Invalid rpm and amplitude combination");
        valid = 0;
    }

    else if (rpm > 120){
        ESP_LOGE(TAG, "Invalid rpm value");
        send_error_message("Invalid rpm value");
        valid = 0;
    }

    return valid;

}