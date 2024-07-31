
# SPIRABOT src

*This code is still under development.

## 🧐 About

This is the source code for the SPIRABOT. The SPIRABOT is controlled through uart (see the UART_controller.py in the root of this repo for examples).

```bash
./
└── src
    ├── channels.h
    ├── io.c 
    ├── io.h 
    ├── robot.c
    ├── robot.h
    ├── state_machine.c
    ├── state_machine.h
    ├── stepper_motor_encoder.c
    ├── stepper_motor_encoder.h
    ├── uart.c
    ├── uart.h
    └── main.py
```

# channels.h

## Channel Definitions for SpiraBot Control

This file provides the channel definitions for controlling the SpiraBot. The definitions include pin numbers and selection values for different channels used in the control process.

## Pin Definitions

- `BUTTON_BACK_STOP_PIN`: The pin number for the back stop button.
- `OPTICAL_SWITCH_PIN`: The pin number for the optical switch.
- `STEP_MOTOR_ENABLE_PIN`: The pin number for the step motor enable channel.
- `STEP_MOTOR_DIR_PIN`: The pin number for the step motor direction channel.
- `STEP_MOTOR_STEP_PIN`: The pin number for the step motor step channel.

## Selection Values

- `BUTTON_BACK_STOP_SEL`: The selection value for the back stop button pin.
- `OPTICAL_SWITCH_SEL`: The selection value for the optical switch pin.
- `STEP_MOTOR_ENABLE_SEL`: The selection value for the step motor enable pin.
- `STEP_MOTOR_DIR_SEL`: The selection value for the step motor direction pin.
- `STEP_MOTOR_STEP_SEL`: The selection value for the step motor step pin.

## Other Definitions

- `ESP_INTR_FLAG_DEFAULT`: The default interrupt flag value for ESP32.
- `STEP_MOTOR_ENABLE_LEVEL`: The logic level value for enabling the step motor.
- `STEP_MOTOR_DISABLE_LEVEL`: The logic level value for disabling the step motor.
- `STEP_MOTOR_SPIN_DIR_OUT`: The direction value for the step motor to spin outward.
- `STEP_MOTOR_SPIN_DIR_IN`: The direction value for the step motor to spin inward.
- `STEP_MOTOR_RESOLUTION_HZ`: The resolution in hertz for the step motor.

## Usage

1. Include the `channel_definitions.h` header file in your code:

   ```c
   #include "channels.h"
   ```

*It may be an idea to move other definitions to this header file as well. For simplicity..

# io.c / io.h

This code initializes IO pins for motor control and button inputs.
## Usage
Call the `io_init()` function to initialize the IO pins:

```c
int main(void) {
    // Other code...

    // Initialize IO pins
    io_init();

    // Other code...

    return 0;
}
````
## Functionality

The io_init() function initializes the motor step pin, enable pin, and button pins for input.
It sets the appropriate GPIO configurations for each pin.

# robot.c/ robot.h

## Usage
Call the `robot_init()` function to initialize the hardware:
```c
int main(void) {
    // Other code...

    // Initialize hardware
    robot_init();

    // Other code...

    return 0;
}
````

## Running the motor
```c
#include "robot.h"
int main(void){
    robot_motor_set_dir(DIR_OUT, &last_dir, &current_dir);
    robot_motor_do_steps_2(300, 50, 5, 100);
}
````
This code will run the motor for a total of `300` steps. The start speed (frequenzy) is set to `50` steps/second (0.5mm/second). The acceleration is set to 5hz/step and the acceleration periode will last for 100 steps (1/3) of the total steps. 

*Some fundtions needed to make sure that the motor speed/acc is accidentaly set to high. Also a function that sets the mtor variables based in a desired frequenzy need to be implememntet. 

Use the provided functions to control the SpiraBot:
- `void robot_motor_set_dir(robot_motor_dir_t new_dir, robot_motor_dir_t *last_dir, robot_motor_dir_t *current_dir)`
  - Set the motor direction.
  - Parameters:
    - `new_dir (robot_motor_dir_t)`: New direction to set.
    - `last_dir (robot_motor_dir_t*)`: Pointer to the last direction.
    - `current_dir (robot_motor_dir_t*)`: Pointer to the current direction.
- `void robot_motor_run_to_back_stop(int speed)`
  - Run the motor to the back stop.
  - Parameters:
    - `speed (int)`: Speed of the motor.
- `int robot_motor_do_steps_2(int steps, int speed, int increment, int accel_steps)`
  - Perform a specific number of motor steps with acceleration.
  - Parameters:
    - `steps (int)`: Number of steps to perform.
    - `speed (int)`: Start speed of the motor.
    - `increment (int)`: Frequency increment per step.
    - `accel_steps (int)`: Number of steps for acceleration phase.
- `int robot_button_get_back_stop_signal(void)`
  - Get the status of the back stop button.
  - Returns:
    - int: 1 if the button is pushed, 0 otherwise.
- `int mm_to_steps(float mm)`
  - Convert millimeters to motor steps.
  - Parameters:
    - `mm (float)`: Length in millimeters.
  - Returns:
    - int: Equivalent number of motor steps.

## The functions belove are also in the code, but will be edited soon. 
*We need to decide how and where to store the robot variables. This functions are made to edit a config variable of type `robot_config_t`(Defined in robot.h), but this variable is not used to hold the robot settings. At the moment the robot settings are stored in uart.c, because it is there they are updated. The robot.c is currently just a slave reading the variables from uart.

- `void robot_set_config(robot_config_t config)`
  - Set the robot configuration.
  - Parameters:
    - `config (robot_config_t)`: Configuration to set.
- `void robot_motor_set_speed(int speed)`
  - Set the motor speed.
  - Parameters:
    - `speed (int)`: Speed of the motor.
- `robot_config_t robot_get_config(void)`
  - Get the robot configuration.
  - Returns:
    - robot_config_t: Robot configuration.

## Functionality

The code initializes the hardware and provides functions to control the SpiraBot motor and handle button input.
It uses RMT (Remote Control) channels for motor control and provides options for acceleration and speed adjustment.


# state_machine.c/ state_machine.h

This code provides the implementation of a state machine for controlling the SpiraBot. The state machine manages the different states of the robot and transitions between them based on certain conditions.

*state_machine.c and uart.c currenlty shares three variables without mutex protection. This needs to be fixed to avoid future bugs.

## Constants

- `STEPS_TO_ORIGO`: The number of steps required to reach the origin position from the back stop button.
- `BREATH_START_STATE`: The initial state for the breathing process.
- `INIT_MOTOR_SPEED_HZ_FAST`: The initial motor speed in hertz for fast movement during initialization.
- `INIT_MOTOR_SPEED_HZ_SLOW`: The initial motor speed in hertz for slow movement during initialization.
- `INIT_STEPS`: The number of steps to release the backstop during initialization.

## Enumerations

- `robot_state_t`: An enumeration representing the different states of the robot.
- The states are:
  - `STATE_INIT`
  - `STATE_IDLE`
  - `STATE_BREATHING`
  - `STATE_INHALE`
  - `STATE_EXHALE`
  - `STATE_STOP`

## Functions

- `robot_state_t state_machine_do_init(void)`: Performs the initialization process of the robot, including setting the motor direction, running the motor to the backstop, release the backstop, and moving to the origin position.
- `robot_state_t state_machine_do_idle(void)`: Handles the idle state of the robot, continuously checking for conditions to transition to the breathing state.
- `robot_state_t state_machine_do_breathing(void)`: Manages the breathing state of the robot, adjusting the amplitude of the movement and checking for conditions to transition to other states.
- `robot_state_t state_machine_do_inhale(void)`: Performs the inhalation (motor runs out) process of the robot, setting the motor direction and performing the required number of steps.
- `robot_state_t state_machine_do_exhale(void)`: Performs the exhalation (motor runs in) process of the robot, setting the motor direction and performing the required number of steps.
- `robot_state_t state_machine_do_stop(void)`: Handles the stop state of the robot, setting the motor direction to stop.

## Usage

1. Include the `state_machine.h` header in your code:

   ```c
   #include "state_machine.h"
