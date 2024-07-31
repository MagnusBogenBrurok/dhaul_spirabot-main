#include <stddef.h>

#ifndef STATE_MACHINE_H
#define STATE_MACHINE_H

#define STORAGE_NAMESPACE "storage"
#define DEFAULT_SERIAL_NUMBER "AB1G-XXXX-XXXX"

#define INIT_MOTOR_SPEED_HZ_FAST 600 * 8
#define INIT_MOTOR_SPEED_HZ_SLOW 100 * 8
#define INIT_STEPS 100 // 1.0 mm

#define DEFAULT_CURVE_MODE SINE_WAVE

#define MAX_SINE_WAVE_VAL_LENGTH 6010       // Example maximum
#define MAX_SINE_WAVE_RESAMP_LENGTH 8010    // Example maximum
#define MAX_SINE_WAVE_FREQ_LIST_LENGTH 8010 // Example maximum

typedef enum
{
    STATE_INIT = 0,
    STATE_IDLE = 1,
    STATE_MOVE_ORIGO = 2,
    STATE_SINE_WAVE = 3,
    STATE_ERROR = 4,
} robot_state_t;

typedef enum
{
    CUSTOM_WAVE = 0,
    SINE_WAVE = 1,
    MANUAL = 2,
} curve_mode_t;

typedef struct
{
    int stop_flag;
    int init_flag;
    int update_flag;
} action_flag_t;

void state_machine_loop(void *pvParameters);
robot_state_t state_machine_do_init(void);
robot_state_t state_machine_do_sine_wave(void);
robot_state_t state_machine_do_idle(void);
robot_state_t state_machine_do_move_origo(void);
robot_state_t state_machine_do_error(void);
int32_t read_value(const char *key);
void save_value(const char *key, int32_t value);
void save_serial_number(const char* serial_number);
void get_serial_number(char* serial_number, size_t max_len);
int parameter_validtion_check(float amplitude, float rpm, int microstep);

#endif