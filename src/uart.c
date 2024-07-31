#include "uart.h"
#include "robot.h"
#include "state_machine.h"
#include "waveform.h"
#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "driver/uart.h"
#include "esp_log.h"
#include "cJSON.h"
#include <sys/select.h>
#include <unistd.h>
#include "freertos/semphr.h"

extern robot_config_t robot_config;
extern action_flag_t action_flags;
extern waveform_sine_encoder_config_t sine_encoder_config;
extern curve_mode_t curve_mode;
extern robot_state_t current_state;
const char *TAG = "UART";

static void handle_set_microstep(cJSON *root);
static void handle_set_curve_mode(cJSON *root);
static void handle_set_rpm(cJSON *root);
static void handle_set_amp(cJSON *root);
static void handle_set_curve_type(cJSON *root);
static void handle_set_amnesia(cJSON *root);
static void handle_run_to_slot(cJSON *root);
static void handle_run_to_abs_pos(cJSON *root);
static void handle_run_to_rel_pos(cJSON *root);
static void handle_stop(cJSON *root);
static void handle_init(cJSON *root);
static void handle_send_status(cJSON *root);
static void handle_set_serial_number(cJSON *root);

void uart_config()
{
    ESP_LOGI(TAG, "uart_config");
    uart_config_t uartConfig = {
        .baud_rate = 115200,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE};
    uart_param_config(EX_UART_NUM, &uartConfig);
    uart_set_pin(EX_UART_NUM, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
    uart_driver_install(EX_UART_NUM, BUF_SIZE * 10, 0, 0, NULL, 0);

}


void uart_task(void *pvParameters)
{
    printf("testing printf\n");
    if (USE_UART == false)
        {
        ESP_LOGI(TAG, "UART is disabled\n");
        printf("UART is disabled\n");
        
        while(1)
        {
            char buffer[128];
            if (fgets(buffer, sizeof(buffer), stdin) != NULL) {
                // Do something with the input
                ESP_LOGI(TAG, "Received message");
                printf("Received message\n");
                cJSON *root = cJSON_Parse(buffer);
                if (root != NULL){
                    handle_set_serial_number(root);
                    handle_set_microstep(root);
                    handle_set_curve_mode(root);
                    handle_set_rpm(root);
                    handle_set_amp(root);
                    handle_set_curve_type(root);
                    handle_set_amnesia(root);
                    handle_run_to_slot(root);
                    handle_run_to_abs_pos(root);
                    handle_run_to_rel_pos(root);
                    handle_stop(root);
                    handle_init(root);
                    handle_send_status(root);
                }
            }
            vTaskDelay(pdMS_TO_TICKS(100));
        }
        }

    else 
    {
        uart_config();
        uint8_t *data = (uint8_t *)malloc(BUF_SIZE);

        while (1)
        {
            int len = uart_read_bytes(EX_UART_NUM, data, BUF_SIZE, 20 / portTICK_RATE_MS);
            if (len > 0)
            {   
                ESP_LOGI(TAG, "Received %d bytes", len);
                cJSON *root = cJSON_Parse((char *)data);
                if (root != NULL)
                {
                    handle_set_serial_number(root);
                    handle_set_microstep(root);
                    handle_set_curve_mode(root);
                    handle_set_rpm(root);
                    handle_set_amp(root);
                    handle_set_curve_type(root);
                    handle_set_amnesia(root);
                    handle_run_to_slot(root);
                    handle_run_to_abs_pos(root);
                    handle_run_to_rel_pos(root);
                    handle_stop(root);
                    handle_init(root);
                    handle_send_status(root);
                }

                cJSON_Delete(root);
            }
            vTaskDelay(pdMS_TO_TICKS(100));
        }
        free(data);
        vTaskDelete(NULL);

    }
}

static void handle_set_serial_number(cJSON *root)
{
    cJSON *serial_number = cJSON_GetObjectItem(root, "serial_number");
    if (cJSON_IsString(serial_number))
    {
        ESP_LOGI(TAG, "Serial number: %s", serial_number->valuestring);
        save_serial_number(serial_number->valuestring);
    }
}

static void handle_set_microstep(cJSON *root)
{
    cJSON *micro_step = cJSON_GetObjectItem(root, "micro_step");
    if (cJSON_IsNumber(micro_step))
    {
        ESP_LOGI(TAG, "micro_step: %d", micro_step->valueint);
        robot_motor_set_microstepping(micro_step->valueint, &robot_config);
    }
}

static void handle_set_curve_mode(cJSON *root)
{
    cJSON *mode = cJSON_GetObjectItem(root, "curve_mode");
    if (cJSON_IsNumber(mode))
    {
        ESP_LOGI(TAG, "curve_mode: %d", mode->valueint);
        int temp_curve_mode = mode->valueint;
        if (temp_curve_mode)
        {
            curve_mode = temp_curve_mode;
        }
    }
}

static void handle_set_rpm(cJSON *root)
{
    cJSON *rpm_json = cJSON_GetObjectItem(root, "rpm");
    if (cJSON_IsNumber(rpm_json))
    {
        ESP_LOGI(TAG, "rpm: %f", rpm_json->valuedouble);
        sine_encoder_config.rpm = (float)rpm_json->valuedouble;
        sine_encoder_config.time_duration = -1;
    }
}

static void handle_set_amp(cJSON *root)
{
    cJSON *amplitude_json = cJSON_GetObjectItem(root, "amp");
    if (cJSON_IsNumber(amplitude_json))
    {
        ESP_LOGI(TAG, "amp: %f", amplitude_json->valuedouble);
        sine_encoder_config.amplitude = (float)amplitude_json->valuedouble;
    }
}

static void handle_set_curve_type(cJSON *root)
{
    cJSON *curve_type_json = cJSON_GetObjectItem(root, "curve_type");
    if (cJSON_IsNumber(curve_type_json))
    {
        ESP_LOGI(TAG, "curve_type: %d", curve_type_json->valueint);
        sine_encoder_config.curve_type = (int)curve_type_json->valueint;
    }
}

static void handle_set_amnesia(cJSON *root)
{
    cJSON *amnesia = cJSON_GetObjectItem(root, "amnesia");
    if (cJSON_IsNumber(amnesia))
    {
        if (amnesia->valueint == 1)
        {
            ESP_LOGI(TAG, "amnesia: %d", amnesia->valueint);
            save_value("amnesia", 1);
        }
        else
        {
            ESP_LOGI(TAG, "amnesia: %d", amnesia->valueint);
            save_value("amnesia", 0);
        }
        ESP_LOGI(TAG, "amnesia: %d", amnesia->valueint);
    }
}

static void handle_run_to_slot(cJSON *root)
{
    cJSON *run_to_slot = cJSON_GetObjectItem(root, "run_to_slot");
    if (cJSON_IsNumber(run_to_slot))
    {
        robot_motor_run_to_slot(50, &robot_config);
    }
}

static void handle_run_to_abs_pos(cJSON *root)
{
    cJSON *abs_pos = cJSON_GetObjectItem(root, "abs_pos");
    if (cJSON_IsNumber(abs_pos))
    {
        robot_config.origo = (float)abs_pos->valuedouble;
    }
}

static void handle_run_to_rel_pos(cJSON *root)
{
    cJSON *rel_pos = cJSON_GetObjectItem(root, "rel_pos");
    if (cJSON_IsNumber(rel_pos))
    {
        robot_config.origo = robot_config.origo + (float)rel_pos->valuedouble;
    }
}

static void handle_stop(cJSON *root)
{
    cJSON *stop = cJSON_GetObjectItem(root, "stop");
    if (cJSON_IsNumber(stop))
    {
        ESP_LOGI(TAG, "stop: %d", stop->valueint);
        if ((stop->valueint == 0) && (current_state == STATE_SINE_WAVE)){
            action_flags.update_flag = 1;
            action_flags.stop_flag = 1;
        }
        else{
            action_flags.stop_flag = stop->valueint;
        }
        sine_encoder_config.time_duration = -1;
    }
}

static void handle_init(cJSON *root)
{
    cJSON *init = cJSON_GetObjectItem(root, "init");
    if (cJSON_IsNumber(init))
    {
        ESP_LOGI(TAG, "init: %d", init->valueint);
        action_flags.init_flag = init->valueint;
    }
}

static void handle_send_status(cJSON *root)
{
    cJSON *status = cJSON_GetObjectItem(root, "status_request");
    if (cJSON_IsString(status))
    {   
        fflush(stdout);
        uart_flush(EX_UART_NUM);
        vTaskDelay(pdMS_TO_TICKS(50));
        const char *cmd = status->valuestring;
        uart_flush(EX_UART_NUM);
        vTaskDelay(pdMS_TO_TICKS(50));
        char message[64];
        const char *status_prefix = "***STATUS***"; // Prefix for status messages

        if (strcmp(cmd, "current_pos") == 0)
        {
            snprintf(message, sizeof(message), "%f\n", robot_config.current_pos);
        }
        else if (strcmp(cmd, "fw_hash") == 0)
        {
            snprintf(message, sizeof(message), "%s\n", GIT_COMMIT_ID);
        }
        else if (strcmp(cmd, "current_state") == 0)
        {
            snprintf(message, sizeof(message), "%d\n", current_state);
            ESP_LOGI(TAG, "current_state: %d", current_state);
        }
        else if (strcmp(cmd, "amp") == 0)
        {
            snprintf(message, sizeof(message), "%f\n", sine_encoder_config.amplitude);
        }
        else if (strcmp(cmd, "rpm") == 0)
        {
            snprintf(message, sizeof(message), "%f\n", sine_encoder_config.rpm);
        }
        else if (strcmp(cmd, "curve_type") == 0)
        {
            snprintf(message, sizeof(message), "%d\n", sine_encoder_config.curve_type);
        }
        else if (strcmp(cmd, "error") == 0)
        {
            snprintf(message, sizeof(message), "%d\n", robot_config.error);
        }
        else if (strcmp(cmd, "micro_step") == 0)
        {
            snprintf(message, sizeof(message), "%d\n", robot_config.microstep);
        }
        else if (strcmp(cmd, "curve_mode") == 0)
        {
            snprintf(message, sizeof(message), "%d\n", curve_mode);
        }
        else if (strcmp(cmd, "origo") == 0)
        {
            snprintf(message, sizeof(message), "%f\n", robot_config.origo);
        }
        else if (strcmp(cmd, "serial_number") == 0)
        {
            char serial_number[15];
            get_serial_number(serial_number, 15);
            snprintf(message, sizeof(message), "%s\n", serial_number);
        }

        // Print the prefixed message to the console
        printf("%s%s", status_prefix, message);
    }
}

void send_error_message(const char *message)
{
    const char *error_prefix = "***ERROR***"; // Prefix for error messages
    printf("%s%s\n", error_prefix, message);
}