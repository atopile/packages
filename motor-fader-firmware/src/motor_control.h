/*
 * Motor Control Module
 * 
 * Controls the DRV8210P H-bridge driver for bidirectional motor control.
 * Uses PWM on IN1/IN2 for speed control and direction.
 */

#ifndef MOTOR_CONTROL_H
#define MOTOR_CONTROL_H

#include <zephyr/kernel.h>
#include <stdint.h>
#include <stdbool.h>

/* Motor direction */
typedef enum {
    MOTOR_DIR_STOP = 0,
    MOTOR_DIR_FORWARD,
    MOTOR_DIR_REVERSE,
    MOTOR_DIR_BRAKE
} motor_direction_t;

/* Motor state */
typedef struct {
    bool enabled;
    motor_direction_t direction;
    uint8_t speed;  /* 0-100% */
    int16_t pwm_value;  /* Internal PWM value */
} motor_state_t;

/**
 * Initialize the motor control subsystem
 * @return 0 on success, negative error code on failure
 */
int motor_init(void);

/**
 * Enable or disable the motor driver (nSLEEP pin)
 * @param enable true to enable, false to put driver to sleep
 */
void motor_enable(bool enable);

/**
 * Check if motor driver is enabled
 * @return true if enabled
 */
bool motor_is_enabled(void);

/**
 * Set motor direction and speed
 * @param direction Motor direction (STOP, FORWARD, REVERSE, BRAKE)
 * @param speed Speed percentage (0-100)
 */
void motor_set(motor_direction_t direction, uint8_t speed);

/**
 * Set motor output directly with signed value
 * @param value Motor output (-100 to +100, negative = reverse)
 */
void motor_set_output(int8_t value);

/**
 * Stop the motor (coast)
 */
void motor_stop(void);

/**
 * Brake the motor (both outputs high)
 */
void motor_brake(void);

/**
 * Get current motor state
 * @return Pointer to motor state structure
 */
const motor_state_t* motor_get_state(void);

#endif /* MOTOR_CONTROL_H */

