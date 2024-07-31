#include "io.h"
#include "channels.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"

#include "esp_log.h"

const char *TAG2 = "SLOT_MAP_HANDLER";


int io_init(void){
    // initialize the motor step pin and enable pin
    gpio_config_t en_dir_gpio_config = {
        .mode = GPIO_MODE_OUTPUT,
        .intr_type = GPIO_INTR_DISABLE,
        .pin_bit_mask = STEP_MOTOR_DIR_SEL | STEP_MOTOR_ENABLE_SEL,
    };
    ESP_ERROR_CHECK(gpio_config(&en_dir_gpio_config));

    gpio_config_t m0_m1_gpio_config = {
        .mode = GPIO_MODE_OUTPUT,
        .intr_type = GPIO_INTR_DISABLE,
        .pin_bit_mask = STEP_MOTOR_M0_SEL | STEP_MOTOR_M1_SEL | LED_SEL,
    };
    ESP_ERROR_CHECK(gpio_config(&m0_m1_gpio_config));

    gpio_config_t nsleep_gpio_config = {
        .mode = GPIO_MODE_OUTPUT,
        .intr_type = GPIO_INTR_DISABLE,
        .pin_bit_mask = STEP_MOTOR_NSLEEP_SEL,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&nsleep_gpio_config));

    gpio_config_t io_conf;
    io_conf.intr_type = GPIO_INTR_DISABLE;
    io_conf.mode = GPIO_MODE_INPUT;
    io_conf.pin_bit_mask = BUTTON_TOUCH_SEL;
    io_conf.pull_up_en = GPIO_PULLUP_DISABLE;
    io_conf.pull_down_en = GPIO_PULLDOWN_ENABLE;
    
    ESP_ERROR_CHECK(gpio_config(&io_conf));
    
    io_conf.intr_type = GPIO_INTR_DISABLE;
    io_conf.mode = GPIO_MODE_INPUT;
    io_conf.pin_bit_mask = BUTTON_BACK_STOP_SEL;
    io_conf.pull_up_en = GPIO_PULLUP_ENABLE;
    io_conf.pull_down_en = GPIO_PULLDOWN_DISABLE;
    
    ESP_ERROR_CHECK(gpio_config(&io_conf));

    gpio_config_t io_conf_2;
    io_conf_2.intr_type = GPIO_INTR_NEGEDGE;
    io_conf_2.mode = GPIO_MODE_INPUT;
    io_conf_2.pin_bit_mask = OPTICAL_SWITCH_SEL;
    io_conf_2.pull_up_en = GPIO_PULLUP_ENABLE;
    io_conf_2.pull_down_en = GPIO_PULLDOWN_DISABLE;

    ESP_ERROR_CHECK(gpio_config(&io_conf_2));


    return 1;
}