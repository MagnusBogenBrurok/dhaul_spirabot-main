#include "robot.h"
#include "waveform.h"
#include "channels.h"
#include "io.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "stepper_motor_encoder.h"
#include "driver/rmt_tx.h"
#include "driver/gpio.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <math.h>
#include "esp_timer.h"
#include "esp_sleep.h"
#include "sdkconfig.h"
#include "freertos/task.h"
#include "esp_attr.h"

static const char *TAG = "ROBOT";

rmt_channel_handle_t motor_chan;
rmt_channel_handle_t motor_curve_chan;
rmt_tx_channel_config_t tx_chan_config;
rmt_tx_channel_config_t tx_curve_chan_config;

extern int sine_wave_freq_list;

int robot_init(robot_config_t *robot_config)
{
    // Init hardware
    if (!io_init())
        return 0;

    robot_motor_set_microstepping(DEFAULT_MICRO_STEP, robot_config);

    robot_config->current_pos = 0;
    robot_config->current_dir = DIR_STOP;
    robot_config->error = 0;
    robot_config->origo = INIT_ORIGO; // Totalt steps: 2141*8 = 17128
    robot_config->step_length = (float)(STANDARD_STEP_LENGTH_MM / DEFAULT_MICRO_STEP);
    robot_config->microstep = DEFAULT_MICRO_STEP;

    tx_chan_config.clk_src = RMT_CLK_SRC_DEFAULT; // select clock source
    tx_chan_config.gpio_num = STEP_MOTOR_STEP_PIN;
    tx_chan_config.mem_block_symbols = 64;
    tx_chan_config.resolution_hz = STEP_MOTOR_RESOLUTION_HZ;
    tx_chan_config.trans_queue_depth = 100; // set the number of transactions that can be pending in the background

    tx_curve_chan_config.clk_src = RMT_CLK_SRC_DEFAULT; // select clock source
    tx_curve_chan_config.gpio_num = STEP_MOTOR_STEP_PIN;
    tx_curve_chan_config.mem_block_symbols = 64;
    tx_curve_chan_config.resolution_hz = STEP_MOTOR_RESOLUTION_HZ;
    tx_curve_chan_config.trans_queue_depth = 100; // set the number of transactions that can be pending in the background

    return 1;
}

void robot_motor_init(robot_config_t *robot_config)
{
    for (int i = 0; i < 3; i++) {
        // Toggle LED
        robot_set_LED(1);
        vTaskDelay(pdMS_TO_TICKS(200));  // Delay for 500ms (half a second)
        robot_set_LED(0);
        vTaskDelay(pdMS_TO_TICKS(200));  // Delay for 500ms (half a second)
    }
    robot_set_LED(1);
    robot_motor_sleep(0);
    ESP_LOGI(TAG, "Initialize motor");

    if (robot_backstop_is_pushed())
    {
        ESP_LOGI(TAG, "Backstop button is pushed");
        robot_motor_go_to_rel_pos_mm(0.2, 50, robot_config);
        if (robot_backstop_is_pushed())
        {
            ESP_LOGI(TAG, "Backstop button still pushed. Something is wrong..");
        }
    }

    ESP_LOGI(TAG, "Go to backstop");
    robot_motor_go_to_abs_pos_mm(-1, 50, robot_config);
    vTaskDelay(pdMS_TO_TICKS(1000));

    robot_motor_go_to_abs_pos_mm(10, 50, robot_config);
    vTaskDelay(pdMS_TO_TICKS(1000));
    robot_motor_run_to_slot(50, robot_config);
    vTaskDelay(pdMS_TO_TICKS(1000));
    robot_motor_go_to_rel_pos_mm(-0.2, 20, robot_config);
    robot_config->origo = robot_config->current_pos;

    robot_motor_set_dir(DIR_STOP, robot_config);
    robot_set_LED(0);
}

void robot_set_LED(int state)
{
    // Active low
    int active;
    if (state == 0){
        active = 1;
    }
    else {
        active = 0;
    }
    gpio_set_level(LED_PIN, active);
}

void robot_motor_sleep(int state){
    int active;
    if (state == 0){
        active = 1;
    }
    else
    {
        active = 0;
    }
    
    gpio_set_level(STEP_MOTOR_NSLEEP_PIN, active);
}

motor_dir_t robot_motor_set_dir(motor_dir_t dir, robot_config_t *robot_config)
{
    switch (dir)
    {
    case DIR_IN:
        gpio_set_level(STEP_MOTOR_DIR_PIN, STEP_MOTOR_SPIN_DIR_IN);
        gpio_set_level(STEP_MOTOR_ENABLE_PIN, STEP_MOTOR_ENABLE_LEVEL);
        robot_config->current_dir = DIR_IN;
        ESP_LOGV(TAG, "Enable step motor -> SPIN_DIR_IN");
        break;
    case DIR_OUT:
        gpio_set_level(STEP_MOTOR_ENABLE_PIN, STEP_MOTOR_ENABLE_LEVEL);
        gpio_set_level(STEP_MOTOR_DIR_PIN, STEP_MOTOR_SPIN_DIR_OUT);
        robot_config->current_dir = DIR_OUT;
        ESP_LOGV(TAG, "Enable step motor -> SPIN_DIR_OUT");
        break;
    case DIR_STOP:
        gpio_set_level(STEP_MOTOR_ENABLE_PIN, STEP_MOTOR_DISABLE_LEVEL);
        robot_config->current_dir = DIR_STOP;
        ESP_LOGV(TAG, "Disable step motor");
        break;
    default:
        break;
    }
    return dir;
}

int robot_backstop_is_pushed(void)
{ // 1 = active, 0 = not active
    int active;
    int not_active;

    if(DOUBLE_OPTICAL_SENSOR_PCB){
        active = 0;
        not_active = 1;
    }
    else{
        active = 1;
        not_active = 0;
    }
    if (gpio_get_level(BUTTON_BACK_STOP_PIN))
        return not_active;
    return active;
}

int robot_optical_is_open(void)
{
    // Return 1 if switch detects open slot
    if (gpio_get_level(OPTICAL_SWITCH_PIN))
        return 0;
    else
        return 1;
}

int robot_touch_is_pushed(void)
{
    // Return 1 if switch detects open slot
    if (gpio_get_level(BUTTON_TOUCH_PIN))
        return 1;
    else
        return 0;
}

void robot_motor_set_microstepping(int enable, robot_config_t *robot_config)
{
    switch (enable)
    {
    case 1: // Full step
        gpio_set_level(STEP_MOTOR_M0_PIN, 0);
        gpio_set_level(STEP_MOTOR_M1_PIN, 0);
        robot_config->step_length = (float)(STANDARD_STEP_LENGTH_MM);
        robot_config->microstep = 1;
        break;

    case 2: // Half step
        gpio_set_level(STEP_MOTOR_M0_PIN, 1);
        gpio_set_level(STEP_MOTOR_M1_PIN, 0);
        robot_config->step_length = (float)(STANDARD_STEP_LENGTH_MM / 2.0);
        robot_config->microstep = 2;
        break;

    case 8: // 1/8 step
        gpio_set_level(STEP_MOTOR_M0_PIN, 0);
        gpio_set_level(STEP_MOTOR_M1_PIN, 1);
        robot_config->step_length = (float)(STANDARD_STEP_LENGTH_MM / 8.0);
        robot_config->microstep = 8;
        break;

    default:
        break;
    }
}

void robot_motor_do_curve(int *stop_flag, int *curve, int curve_length, robot_config_t *robot_config)
{
    ESP_LOGI(TAG, "Robot_do_steps");
    ESP_LOGI(TAG, "Create motor encoders");
    rmt_channel_handle_t motor_curve_chan = NULL;

    stepper_motor_custom_encoder_config_t encoder_config = {
        .resolution = STEP_MOTOR_RESOLUTION_HZ,
        .sample_points = curve_length,
        .curve = curve,
    };

    rmt_encoder_handle_t motor_encoder = NULL;

    ESP_ERROR_CHECK(rmt_new_stepper_motor_custom_encoder(&encoder_config, &motor_encoder));
    // int speed = standard_curve_config.speed_hz*robot_config.micro_steps;

    ESP_ERROR_CHECK(rmt_new_tx_channel(&tx_curve_chan_config, &motor_curve_chan));

    ESP_ERROR_CHECK(rmt_enable(motor_curve_chan));

    rmt_transmit_config_t tx_config = {
        .loop_count = 0,
    };

    // int iterations = 1;
    while (*stop_flag == 0)
    {
        robot_motor_set_dir(DIR_OUT, robot_config);
        robot_set_LED(1);
        ESP_ERROR_CHECK(rmt_transmit(motor_curve_chan, motor_encoder, &encoder_config.sample_points, sizeof(encoder_config.sample_points), &tx_config));

        // ESP_LOGI(TAG, "transmitt to motor");
        ESP_ERROR_CHECK(rmt_tx_wait_all_done(motor_curve_chan, -1));
        // ESP_LOGI(TAG, "motor transmitt done");
        robot_config->current_pos += encoder_config.sample_points;

        robot_motor_set_dir(DIR_IN, robot_config);
        robot_set_LED(0);

        // ESP_LOGI(TAG, "transmitt to motor");
        ESP_ERROR_CHECK(rmt_transmit(motor_curve_chan, motor_encoder, &encoder_config.sample_points, sizeof(encoder_config.sample_points), &tx_config));

        ESP_ERROR_CHECK(rmt_tx_wait_all_done(motor_curve_chan, -1));
        robot_config->current_pos -= encoder_config.sample_points;
        // ESP_LOGI(TAG, "motor transmitt done");
    }
    ESP_LOGI(TAG, "Disable RMT channel");
    ESP_ERROR_CHECK(rmt_disable(motor_curve_chan));
    ESP_LOGI(TAG, "Delete motor channel");
    ESP_ERROR_CHECK(rmt_del_channel(motor_curve_chan));
}

int robot_motor_run_to_backstop(int speed_hz, robot_config_t *robot_config)
{
    rmt_channel_handle_t motor_chan = NULL;
    if (motor_chan != NULL)
    {
        ESP_LOGI(TAG, "Error! Motor channel is not NULL");
    }
    stepper_motor_uniform_encoder_config_t encoder_config = {
        .resolution = STEP_MOTOR_RESOLUTION_HZ,
    };
    rmt_encoder_handle_t motor_encoder = NULL;
    ESP_ERROR_CHECK(rmt_new_stepper_motor_uniform_encoder(&encoder_config, &motor_encoder));

    rmt_transmit_config_t tx_config = {
        .loop_count = 0,
    };

    ESP_ERROR_CHECK(rmt_new_tx_channel(&tx_chan_config, &motor_chan));
    ESP_ERROR_CHECK(rmt_enable(motor_chan));

    int steps = 0;
    robot_motor_set_dir(DIR_IN, robot_config);
    while (!robot_backstop_is_pushed())
    {
        steps++;
        ESP_ERROR_CHECK(rmt_transmit(motor_chan, motor_encoder, &speed_hz, sizeof(speed_hz), &tx_config));
    };
    robot_motor_set_dir(DIR_STOP, robot_config);

    ESP_ERROR_CHECK(rmt_disable(motor_chan));
    ESP_ERROR_CHECK(rmt_del_channel(motor_chan));
    robot_config->current_pos = 0;
    return steps;
}

int robot_motor_run_to_slot(int speed, robot_config_t *robot_config)
{

    float speed_fraction_of_max = (float)speed / 100.0;
    ESP_LOGI(TAG, "speed_fraction_of_max%f", speed_fraction_of_max);
    int speed_hz = (int)(MAX_SPEED * robot_config->microstep) * speed_fraction_of_max;
    ESP_LOGI(TAG, "speed_hz: %d", speed_hz);
    rmt_channel_handle_t motor_chan = NULL;

    if (motor_chan != NULL)
    {
        ESP_LOGI(TAG, "Error! Motor channel is not NULL");
    }
    stepper_motor_uniform_encoder_config_t encoder_config = {
        .resolution = STEP_MOTOR_RESOLUTION_HZ,
    };
    rmt_encoder_handle_t motor_encoder = NULL;
    ESP_ERROR_CHECK(rmt_new_stepper_motor_uniform_encoder(&encoder_config, &motor_encoder));

    rmt_transmit_config_t tx_config = {
        .loop_count = 0,
    };

    ESP_ERROR_CHECK(rmt_new_tx_channel(&tx_chan_config, &motor_chan));
    ESP_ERROR_CHECK(rmt_enable(motor_chan));

    int steps = 0;
    robot_motor_set_dir(DIR_IN, robot_config);
    while (!robot_optical_is_open())
    {
        steps++;
        ESP_ERROR_CHECK(rmt_transmit(motor_chan, motor_encoder, &speed_hz, sizeof(speed_hz), &tx_config));
        if (robot_backstop_is_pushed()){
            break;
        }

    };
    robot_motor_set_dir(DIR_STOP, robot_config);

    ESP_ERROR_CHECK(rmt_disable(motor_chan));
    ESP_ERROR_CHECK(rmt_del_channel(motor_chan));
    robot_config->current_pos -= steps * robot_config->step_length;
    robot_config->origo = robot_config->current_pos;
    return steps;
}

int robot_motor_go_to_abs_pos_mm(float abs_pos, int speed, robot_config_t *robot_config)
{
    float speed_fraction_of_max = (float)speed / 100.0;
    ESP_LOGI(TAG, "speed_fraction_of_max%f", speed_fraction_of_max);
    int speed_hz = (int)(MAX_SPEED * robot_config->microstep) * speed_fraction_of_max;
    ESP_LOGI(TAG, "speed_hz: %d", speed_hz);
    if (abs_pos == -1)
    {
        robot_motor_run_to_backstop(speed_hz, robot_config);
        return 1;
    }

    // Calculate steps
    float delta_dist = (float)abs_pos - robot_config->current_pos;
    int delta_steps = (int)round(delta_dist / robot_config->step_length);

    // Do steps and update current positin.
    robot_config->current_pos += robot_motor_do_steps(delta_steps, speed_hz, robot_config) * robot_config->step_length;
    return 1;
}

int robot_motor_go_to_rel_pos_mm(float rel_pos, int speed, robot_config_t *robot_config)
{
    float speed_fraction_of_max = (float)speed / 100.0;
    ESP_LOGI(TAG, "speed_fraction_of_max%f", speed_fraction_of_max);
    int speed_hz = (int)(MAX_SPEED * robot_config->microstep) * speed_fraction_of_max;
    ESP_LOGI(TAG, "speed_hz: %d", speed_hz);
    int delta_steps = (int)round(rel_pos / robot_config->step_length);
    robot_config->current_pos += robot_motor_do_steps(delta_steps, speed_hz, robot_config) * robot_config->step_length;
    return 1;
}

int robot_motor_do_steps(int steps, int speed_hz, robot_config_t *robot_config)
{
    rmt_channel_handle_t motor_chan = NULL;
    if (motor_chan != NULL)
    {
        ESP_LOGI(TAG, "Error! Motor channel is not NULL");
    }
    stepper_motor_uniform_encoder_config_t encoder_config = {
        .resolution = STEP_MOTOR_RESOLUTION_HZ,
    };
    rmt_encoder_handle_t motor_encoder = NULL;
    ESP_ERROR_CHECK(rmt_new_stepper_motor_uniform_encoder(&encoder_config, &motor_encoder));

    rmt_transmit_config_t tx_config = {
        .loop_count = 0,
    };

    ESP_ERROR_CHECK(rmt_new_tx_channel(&tx_chan_config, &motor_chan));
    ESP_ERROR_CHECK(rmt_enable(motor_chan));

    if (steps > 0)
    {
        robot_motor_set_dir(DIR_OUT, robot_config);
    }
    else
    {
        robot_motor_set_dir(DIR_IN, robot_config);
    }

    for (int n = 0; n < abs(steps); n++)
    {
        //speed_hz = step_list[n];
        ESP_ERROR_CHECK(rmt_transmit(motor_chan, motor_encoder, &speed_hz, sizeof(speed_hz), &tx_config));
        ESP_ERROR_CHECK(rmt_tx_wait_all_done(motor_chan, -1));
    };

    //robot_config->current_pos += steps * robot_config->step_length;
    robot_motor_set_dir(DIR_STOP, robot_config);

    ESP_ERROR_CHECK(rmt_disable(motor_chan));
    ESP_ERROR_CHECK(rmt_del_channel(motor_chan));
    return steps;
}

