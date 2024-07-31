#ifndef ROBOT_H
#define ROBOT_H

#define INIT_MICROSTEP 8
#define INIT_SPEED_HZ 300
#define INIT_ORIGO 8800

#define BACKSTOP_BUTTON_PADDING_MM 1 
#define SLOT_MAP_SIZE 28

#define STEPS_PER_MM 100
#define STANDARD_STEP_LENGTH_MM 0.01
#define MAX_SPEED 1000

#define CURVE_CONFIG_FREQ 17
#define CURVE_CONFIG_LOOP_COUNT -1
#define CURVE_CONFIG_CURVE_LENGTH -1
#define CURVE_CONFIG_CURVE_LENGTH_MAX 1022  

#define DEFAULT_STOP_FLAG 1
#define DEFAULT_INIT_FLAG 0
#define DEFAULT_UPDATE_FLAG 0

#define DEFAULT_MICRO_STEP 8
#define DEFAULT_AMP 2
#define DEFAULT_SPEED 100  
#define DEFAULT_INHALE_ACC 3   
#define DEFAULT_EXHALE_ACC 3

#define DOUBLE_OPTICAL_SENSOR_PCB true

#include "waveform.h"

typedef enum motor_direction { 
    DIR_IN = -1,
    DIR_STOP = 0,
    DIR_OUT = 1
} motor_dir_t;

typedef enum optical_switch_state {
    OPTICAL_SWITCH_OPEN_SLOT = 1,
    OPTICAL_SWITCH_CLOSED_SLOT = 0
} optical_switch_state_t;

typedef struct {
    char serial_number[15];
    motor_dir_t current_dir;
    float current_pos;
    int error;
    float origo;
    float step_length;
    int microstep;
    int slot_map[SLOT_MAP_SIZE];
} robot_config_t;


int robot_init(robot_config_t *robot_config);

void robot_motor_init(robot_config_t *robot_config);

motor_dir_t robot_motor_set_dir(motor_dir_t dir, robot_config_t *robot_config);

int robot_backstop_is_pushed(void);

int robot_optical_is_open(void);

int robot_touch_is_pushed(void);

void robot_motor_set_microstepping(int enable, robot_config_t *robot_config);

void robot_set_LED(int state);

void robot_motor_sleep(int state);

void robot_motor_do_curve(int *stop_flag, int *curve, int curve_length, robot_config_t *robot_config);

int robot_motor_run_to_backstop(int speed_hz, robot_config_t *robot_config);

int robot_motor_run_to_slot(int speed, robot_config_t *robot_config);

int robot_motor_go_to_abs_pos_mm(float abs_pos, int speed, robot_config_t *robot_config);

int robot_motor_go_to_rel_pos_mm(float rel_pos, int speed, robot_config_t *robot_config);

int robot_motor_do_steps(int steps, int speed, robot_config_t *robot_config);

#endif