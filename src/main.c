#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "esp_log.h"
#include "uart.h"
#include "state_machine.h"
#include "robot.h"


static const char *TAG = "MAIN";

void app_main() {
    vTaskDelay(pdMS_TO_TICKS(1000));
    fflush(stdout);

    // uart_init();
    // usb_cdc_init();
    // redirect_stdout_to_usb();

    // ESP_LOGI(TAG, "Starting main");

    //esp_log_level_set(TAG, ESP_LOG_INFO);
    //esp_log_level_set("gpio", ESP_LOG_NONE);
    //esp_log_level_set("*", ESP_LOG_NONE);

    //ESP_LOGI(TAG, "Starting main");

    // xTaskCreate(usb_task, "usb_task", 4096, NULL, 10, NULL);
    // xTaskCreate(send_task, "USB_SERIAL_JTAG_send_task", ECHO_TASK_STACK_SIZE, NULL, 10, NULL);

    xTaskCreatePinnedToCore(uart_task, "uart_task", 4096, NULL, 2, NULL, 0);
    xTaskCreatePinnedToCore(state_machine_loop, "state_machine_loop", 10*4096, NULL, 1, NULL, 1);

}

