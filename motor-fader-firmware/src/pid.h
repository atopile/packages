/*
 * PID Controller Module
 * 
 * Implements a discrete PID controller with anti-windup
 * for motor fader position control.
 */

#ifndef PID_H
#define PID_H

#include <stdint.h>
#include <stdbool.h>

/* PID configuration structure */
typedef struct {
    float kp;           /* Proportional gain */
    float ki;           /* Integral gain */
    float kd;           /* Derivative gain */
    float output_min;   /* Minimum output value */
    float output_max;   /* Maximum output value */
    float deadband;     /* Error deadband (no output if |error| < deadband) */
    float integral_max; /* Anti-windup: max integral term */
} pid_config_t;

/* PID state structure */
typedef struct {
    pid_config_t config;
    float setpoint;      /* Target value */
    float integral;      /* Accumulated integral term */
    float prev_error;    /* Previous error for derivative */
    float prev_input;    /* Previous input for derivative-on-measurement */
    float output;        /* Last computed output */
    bool enabled;        /* Controller enabled flag */
} pid_state_t;

/**
 * Initialize PID controller with configuration
 * @param pid Pointer to PID state
 * @param config Pointer to configuration (copied)
 */
void pid_init(pid_state_t *pid, const pid_config_t *config);

/**
 * Reset PID controller state (clear integral, etc.)
 * @param pid Pointer to PID state
 */
void pid_reset(pid_state_t *pid);

/**
 * Set PID gains
 * @param pid Pointer to PID state
 * @param kp Proportional gain
 * @param ki Integral gain
 * @param kd Derivative gain
 */
void pid_set_gains(pid_state_t *pid, float kp, float ki, float kd);

/**
 * Set PID setpoint (target)
 * @param pid Pointer to PID state
 * @param setpoint Target value
 */
void pid_set_setpoint(pid_state_t *pid, float setpoint);

/**
 * Enable or disable the PID controller
 * @param pid Pointer to PID state
 * @param enabled true to enable, false to disable
 */
void pid_set_enabled(pid_state_t *pid, bool enabled);

/**
 * Compute PID output
 * @param pid Pointer to PID state
 * @param input Current measured value
 * @param dt Time delta in seconds
 * @return Control output (clamped to output_min/max)
 */
float pid_compute(pid_state_t *pid, float input, float dt);

/**
 * Get current error (setpoint - input)
 * @param pid Pointer to PID state
 * @return Current error value
 */
float pid_get_error(const pid_state_t *pid);

/**
 * Check if controller is at setpoint (within deadband)
 * @param pid Pointer to PID state
 * @param input Current input value
 * @return true if |error| < deadband
 */
bool pid_at_setpoint(const pid_state_t *pid, float input);

#endif /* PID_H */

