#ifndef UART_H
#define UART_H

#define portTICK_RATE_MS (1000 / configTICK_RATE_HZ)
#define EX_UART_NUM UART_NUM_0
#define PATTERN_CHR_NUM (3)

#define BUF_SIZE (1024*2)
#define RD_BUF_SIZE (BUF_SIZE)
#define USE_UART false

#define STORAGE_NAMESPACE "storage"

void uart_config(void);
void tiny_usb_config(void);
void uart_task(void *pvParameters);
void send_status(const char* cmd);
void send_error_message(const char *message);

#endif