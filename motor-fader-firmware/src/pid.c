/*
 * PID Controller Implementation
 * 
 * Features:
 * - Anti-windup with integral clamping
 * - Derivative-on-measurement to avoid derivative kick
 * - Configurable deadband
 * - Output clamping
 */

#include "pid.h"
#include <math.h>

/* Helper to clamp value between min and max */
static inline float clamp(float value, float min, float max)
{
    if (value < min) return min;
    if (value > max) return max;
    return value;
}

void pid_init(pid_state_t *pid, const pid_config_t *config)
{
    if (!pid || !config) {
        return;
    }

    pid->config = *config;
    pid->setpoint = 0.0f;
    pid->integral = 0.0f;
    pid->prev_error = 0.0f;
    pid->prev_input = 0.0f;
    pid->output = 0.0f;
    pid->enabled = false;
}

void pid_reset(pid_state_t *pid)
{
    if (!pid) {
        return;
    }

    pid->integral = 0.0f;
    pid->prev_error = 0.0f;
    pid->prev_input = 0.0f;
    pid->output = 0.0f;
}

void pid_set_gains(pid_state_t *pid, float kp, float ki, float kd)
{
    if (!pid) {
        return;
    }

    pid->config.kp = kp;
    pid->config.ki = ki;
    pid->config.kd = kd;
}

void pid_set_setpoint(pid_state_t *pid, float setpoint)
{
    if (!pid) {
        return;
    }

    pid->setpoint = setpoint;
}

void pid_set_enabled(pid_state_t *pid, bool enabled)
{
    if (!pid) {
        return;
    }

    if (enabled && !pid->enabled) {
        /* Reset state when enabling */
        pid_reset(pid);
    }

    pid->enabled = enabled;
}

float pid_compute(pid_state_t *pid, float input, float dt)
{
    if (!pid || !pid->enabled || dt <= 0.0f) {
        return 0.0f;
    }

    /* Calculate error */
    float error = pid->setpoint - input;

    /* Check deadband */
    if (fabsf(error) < pid->config.deadband) {
        pid->output = 0.0f;
        pid->prev_error = error;
        pid->prev_input = input;
        return 0.0f;
    }

    /* Proportional term */
    float p_term = pid->config.kp * error;

    /* Integral term with anti-windup */
    pid->integral += error * dt;
    pid->integral = clamp(pid->integral, 
                          -pid->config.integral_max, 
                          pid->config.integral_max);
    float i_term = pid->config.ki * pid->integral;

    /* Derivative term (on measurement to avoid derivative kick) */
    float d_input = (input - pid->prev_input) / dt;
    float d_term = -pid->config.kd * d_input;  /* Negative because we use input derivative */

    /* Compute total output */
    float output = p_term + i_term + d_term;

    /* Clamp output */
    output = clamp(output, pid->config.output_min, pid->config.output_max);

    /* Back-calculation anti-windup: if output is saturated, reduce integral */
    if ((output >= pid->config.output_max && error > 0) ||
        (output <= pid->config.output_min && error < 0)) {
        /* Don't accumulate integral when saturated in the wrong direction */
        pid->integral -= error * dt;
    }

    /* Store state for next iteration */
    pid->prev_error = error;
    pid->prev_input = input;
    pid->output = output;

    return output;
}

float pid_get_error(const pid_state_t *pid)
{
    if (!pid) {
        return 0.0f;
    }
    return pid->prev_error;
}

bool pid_at_setpoint(const pid_state_t *pid, float input)
{
    if (!pid) {
        return false;
    }
    
    float error = pid->setpoint - input;
    return fabsf(error) < pid->config.deadband;
}

