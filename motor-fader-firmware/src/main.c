/*
 * Motor Fader Firmware - Main Application
 * 
 * ESP32-S3 + DRV8210P H-bridge + ALPS Motor Fader
 * 
 * Features:
 * - Closed-loop PID position control
 * - Endstop calibration via current sensing
 * - Touch detection and force feedback
 * - Shell commands for testing and tuning
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/adc.h>
#include <zephyr/shell/shell.h>
#include <zephyr/logging/log.h>
#include <zephyr/settings/settings.h>
#include <stdlib.h>
#include <math.h>

#include "motor_control.h"
#include "pid.h"
#include "calibration.h"
#include "touch_detect.h"

LOG_MODULE_REGISTER(main, LOG_LEVEL_INF);

/* ADC configuration */
#define ADC_RESOLUTION      12
#define ADC_MAX_VALUE       ((1 << ADC_RESOLUTION) - 1)  /* 4095 */
#define ADC_REF_MV          3300  /* 3.3V reference */

/* ADC channels */
#define ADC_CHANNEL_POT     1     /* GPIO2 = ADC1_CH1 */
#define ADC_CHANNEL_CURRENT 2     /* GPIO3 = ADC1_CH2 */

/* Control loop timing */
#define CONTROL_LOOP_PERIOD_MS  10    /* 100Hz control loop */
#define ADC_SAMPLE_PERIOD_MS    1     /* 1kHz ADC sampling */

/* Demo mode settings */
#define DEMO_PERIOD_MS          4000  /* Full cycle time for back-and-forth */
#define DEMO_HOLD_TIME_MS       1000  /* Hold at each end */

/* ADC device and channels */
static const struct device *adc_dev;
static struct adc_channel_cfg pot_channel_cfg = {
    .gain = ADC_GAIN_1,
    .reference = ADC_REF_INTERNAL,
    .acquisition_time = ADC_ACQ_TIME_DEFAULT,
    .channel_id = ADC_CHANNEL_POT,
};
static struct adc_channel_cfg current_channel_cfg = {
    .gain = ADC_GAIN_1,
    .reference = ADC_REF_INTERNAL,
    .acquisition_time = ADC_ACQ_TIME_DEFAULT,
    .channel_id = ADC_CHANNEL_CURRENT,
};

/* ADC sequence buffers */
static int16_t pot_sample_buffer;
static int16_t current_sample_buffer;
static struct adc_sequence pot_sequence = {
    .channels = BIT(ADC_CHANNEL_POT),
    .buffer = &pot_sample_buffer,
    .buffer_size = sizeof(pot_sample_buffer),
    .resolution = ADC_RESOLUTION,
};
static struct adc_sequence current_sequence = {
    .channels = BIT(ADC_CHANNEL_CURRENT),
    .buffer = &current_sample_buffer,
    .buffer_size = sizeof(current_sample_buffer),
    .resolution = ADC_RESOLUTION,
};

/* PID controller */
static pid_state_t pid;
static const pid_config_t pid_default_config = {
    .kp = 2.0f,
    .ki = 0.5f,
    .kd = 0.1f,
    .output_min = -100.0f,
    .output_max = 100.0f,
    .deadband = 0.01f,      /* 1% deadband */
    .integral_max = 50.0f,
};

/* Application state */
typedef enum {
    APP_STATE_INIT,
    APP_STATE_DEMO,         /* Motor back-and-forth demo */
    APP_STATE_CALIBRATE,    /* Running calibration */
    APP_STATE_POSITION,     /* Closed-loop position control */
    APP_STATE_MANUAL,       /* Manual control via shell */
    APP_STATE_IDLE
} app_state_t;

static app_state_t app_state = APP_STATE_INIT;
static float target_position = 0.5f;  /* Default to center */
static uint16_t raw_pot_value;
static uint16_t raw_current_value;
static float current_position;

/* Demo state */
static bool demo_direction_forward = true;
static uint32_t demo_last_change;

/* Thread stacks */
K_THREAD_STACK_DEFINE(control_stack, 2048);
static struct k_thread control_thread_data;

/* Synchronization */
K_MUTEX_DEFINE(state_mutex);

/*
 * ADC initialization
 */
static int adc_init(void)
{
    int ret;
    
    adc_dev = DEVICE_DT_GET(DT_NODELABEL(adc0));
    if (!device_is_ready(adc_dev)) {
        LOG_ERR("ADC device not ready");
        return -ENODEV;
    }
    
    /* Configure potentiometer channel */
    ret = adc_channel_setup(adc_dev, &pot_channel_cfg);
    if (ret < 0) {
        LOG_ERR("Failed to setup pot ADC channel: %d", ret);
        return ret;
    }
    
    /* Configure current sense channel */
    ret = adc_channel_setup(adc_dev, &current_channel_cfg);
    if (ret < 0) {
        LOG_ERR("Failed to setup current ADC channel: %d", ret);
        return ret;
    }
    
    LOG_INF("ADC initialized");
    return 0;
}

/*
 * Read ADC values
 */
static int read_adc_values(void)
{
    int ret;
    
    /* Read potentiometer */
    ret = adc_read(adc_dev, &pot_sequence);
    if (ret < 0) {
        LOG_WRN("Pot ADC read failed: %d", ret);
        return ret;
    }
    raw_pot_value = (uint16_t)pot_sample_buffer;
    
    /* Read current sense */
    ret = adc_read(adc_dev, &current_sequence);
    if (ret < 0) {
        LOG_WRN("Current ADC read failed: %d", ret);
        return ret;
    }
    raw_current_value = (uint16_t)current_sample_buffer;
    
    /* Convert to normalized position */
    current_position = calibration_normalize_position(raw_pot_value);
    
    return 0;
}

/*
 * Demo mode - move motor back and forth
 */
static void demo_update(void)
{
    uint32_t now = k_uptime_get_32();
    uint32_t elapsed = now - demo_last_change;
    
    /* Check if it's time to change direction */
    if (elapsed >= (DEMO_PERIOD_MS / 2)) {
        demo_direction_forward = !demo_direction_forward;
        demo_last_change = now;
        
        /* Set new target position */
        target_position = demo_direction_forward ? 0.9f : 0.1f;
        pid_set_setpoint(&pid, target_position);
        
        LOG_INF("Demo: moving to %.1f%%", target_position * 100.0f);
    }
}

/*
 * Control loop thread
 */
static void control_loop_thread(void *p1, void *p2, void *p3)
{
    ARG_UNUSED(p1);
    ARG_UNUSED(p2);
    ARG_UNUSED(p3);
    
    float dt = CONTROL_LOOP_PERIOD_MS / 1000.0f;
    float motor_output;
    
    LOG_INF("Control loop started");
    
    while (1) {
        /* Read sensors */
        if (read_adc_values() < 0) {
            k_msleep(CONTROL_LOOP_PERIOD_MS);
            continue;
        }
        
        /* Process touch detection */
        touch_process(0, raw_current_value, current_position);  /* TODO: actual touch ADC */
        
        k_mutex_lock(&state_mutex, K_FOREVER);
        
        switch (app_state) {
        case APP_STATE_DEMO:
            demo_update();
            /* Fall through to position control */
            __attribute__((fallthrough));
            
        case APP_STATE_POSITION:
            /* Check if user is overriding */
            if (touch_is_touched() && touch_should_yield(raw_current_value)) {
                /* User is pushing - disable motor temporarily */
                motor_stop();
                
                /* In SPRING mode, remember we need to return */
                if (touch_get_ff_mode() == FF_MODE_SPRING) {
                    /* Will spring back when released */
                }
            } else if (touch_get_state() == TOUCH_STATE_RELEASED && 
                       touch_get_ff_mode() == FF_MODE_FOLLOW) {
                /* In follow mode, adopt the new position */
                target_position = current_position;
                pid_set_setpoint(&pid, target_position);
            } else {
                /* Normal PID control */
                motor_output = pid_compute(&pid, current_position, dt);
                motor_set_output((int8_t)motor_output);
            }
            break;
            
        case APP_STATE_CALIBRATE:
            calibration_process(raw_pot_value, raw_current_value);
            if (calibration_get_state() == CAL_STATE_COMPLETE ||
                calibration_get_state() == CAL_STATE_ERROR) {
                /* Calibration finished, return to idle */
                app_state = APP_STATE_IDLE;
            }
            break;
            
        case APP_STATE_MANUAL:
        case APP_STATE_IDLE:
        default:
            /* No automatic control */
            break;
        }
        
        k_mutex_unlock(&state_mutex);
        
        k_msleep(CONTROL_LOOP_PERIOD_MS);
    }
}

/*
 * Shell commands for testing and tuning
 */

/* Start demo mode */
static int cmd_demo(const struct shell *sh, size_t argc, char **argv)
{
    k_mutex_lock(&state_mutex, K_FOREVER);
    
    app_state = APP_STATE_DEMO;
    demo_direction_forward = true;
    demo_last_change = k_uptime_get_32();
    target_position = 0.9f;
    
    motor_enable(true);
    pid_set_enabled(&pid, true);
    pid_set_setpoint(&pid, target_position);
    
    k_mutex_unlock(&state_mutex);
    
    shell_print(sh, "Demo mode started - motor moving back and forth");
    return 0;
}

/* Stop all motor activity */
static int cmd_stop(const struct shell *sh, size_t argc, char **argv)
{
    k_mutex_lock(&state_mutex, K_FOREVER);
    
    app_state = APP_STATE_IDLE;
    motor_stop();
    pid_set_enabled(&pid, false);
    
    k_mutex_unlock(&state_mutex);
    
    shell_print(sh, "Motor stopped");
    return 0;
}

/* Start calibration */
static int cmd_calibrate(const struct shell *sh, size_t argc, char **argv)
{
    k_mutex_lock(&state_mutex, K_FOREVER);
    
    app_state = APP_STATE_CALIBRATE;
    calibration_start();
    
    k_mutex_unlock(&state_mutex);
    
    shell_print(sh, "Calibration started...");
    return 0;
}

/* Set target position */
static int cmd_pos(const struct shell *sh, size_t argc, char **argv)
{
    if (argc < 2) {
        shell_print(sh, "Current position: %.1f%%, Target: %.1f%%",
                    current_position * 100.0f, target_position * 100.0f);
        return 0;
    }
    
    float pos = strtof(argv[1], NULL);
    if (pos < 0.0f || pos > 100.0f) {
        shell_error(sh, "Position must be 0-100");
        return -EINVAL;
    }
    
    k_mutex_lock(&state_mutex, K_FOREVER);
    
    target_position = pos / 100.0f;
    pid_set_setpoint(&pid, target_position);
    
    if (app_state == APP_STATE_IDLE) {
        app_state = APP_STATE_POSITION;
        motor_enable(true);
        pid_set_enabled(&pid, true);
    }
    
    k_mutex_unlock(&state_mutex);
    
    shell_print(sh, "Target position: %.1f%%", pos);
    return 0;
}

/* Set PID gains */
static int cmd_pid(const struct shell *sh, size_t argc, char **argv)
{
    if (argc < 4) {
        shell_print(sh, "Usage: pid <Kp> <Ki> <Kd>");
        shell_print(sh, "Current: Kp=%.2f Ki=%.2f Kd=%.2f",
                    pid.config.kp, pid.config.ki, pid.config.kd);
        return 0;
    }
    
    float kp = strtof(argv[1], NULL);
    float ki = strtof(argv[2], NULL);
    float kd = strtof(argv[3], NULL);
    
    pid_set_gains(&pid, kp, ki, kd);
    pid_reset(&pid);  /* Reset integral when gains change */
    
    shell_print(sh, "PID gains set: Kp=%.2f Ki=%.2f Kd=%.2f", kp, ki, kd);
    return 0;
}

/* Manual motor control */
static int cmd_motor(const struct shell *sh, size_t argc, char **argv)
{
    if (argc < 2) {
        const motor_state_t *state = motor_get_state();
        shell_print(sh, "Motor: enabled=%d dir=%d speed=%d",
                    state->enabled, state->direction, state->speed);
        return 0;
    }
    
    int value = strtol(argv[1], NULL, 10);
    
    k_mutex_lock(&state_mutex, K_FOREVER);
    
    app_state = APP_STATE_MANUAL;
    pid_set_enabled(&pid, false);
    motor_enable(true);
    motor_set_output((int8_t)value);
    
    k_mutex_unlock(&state_mutex);
    
    shell_print(sh, "Motor output: %d", value);
    return 0;
}

/* Show status */
static int cmd_status(const struct shell *sh, size_t argc, char **argv)
{
    const motor_state_t *motor = motor_get_state();
    const calibration_data_t *cal = calibration_get_data();
    
    shell_print(sh, "=== Motor Fader Status ===");
    shell_print(sh, "App state: %d", app_state);
    shell_print(sh, "Motor: enabled=%d dir=%d speed=%d",
                motor->enabled, motor->direction, motor->speed);
    shell_print(sh, "Position: raw=%d normalized=%.1f%% target=%.1f%%",
                raw_pot_value, current_position * 100.0f, target_position * 100.0f);
    shell_print(sh, "Current: raw=%d", raw_current_value);
    shell_print(sh, "Touch: state=%d", touch_get_state());
    
    if (cal) {
        shell_print(sh, "Calibration: min=%d max=%d", cal->pos_min, cal->pos_max);
    } else {
        shell_print(sh, "Calibration: not calibrated");
    }
    
    shell_print(sh, "PID: Kp=%.2f Ki=%.2f Kd=%.2f error=%.3f",
                pid.config.kp, pid.config.ki, pid.config.kd,
                pid_get_error(&pid));
    
    return 0;
}

/* Force feedback mode */
static int cmd_ff(const struct shell *sh, size_t argc, char **argv)
{
    if (argc < 2) {
        shell_print(sh, "Force feedback mode: %d", touch_get_ff_mode());
        shell_print(sh, "Modes: 0=disabled, 1=hold, 2=spring, 3=follow");
        return 0;
    }
    
    int mode = strtol(argv[1], NULL, 10);
    if (mode < 0 || mode > 3) {
        shell_error(sh, "Invalid mode");
        return -EINVAL;
    }
    
    touch_set_ff_mode((force_feedback_mode_t)mode);
    shell_print(sh, "Force feedback mode set to %d", mode);
    return 0;
}

/* Register shell commands */
SHELL_STATIC_SUBCMD_SET_CREATE(fader_cmds,
    SHELL_CMD(demo, NULL, "Start demo mode (back and forth)", cmd_demo),
    SHELL_CMD(stop, NULL, "Stop motor", cmd_stop),
    SHELL_CMD(cal, NULL, "Start calibration", cmd_calibrate),
    SHELL_CMD(pos, NULL, "Set/get position (0-100)", cmd_pos),
    SHELL_CMD(pid, NULL, "Set PID gains <Kp> <Ki> <Kd>", cmd_pid),
    SHELL_CMD(motor, NULL, "Manual motor control (-100 to 100)", cmd_motor),
    SHELL_CMD(status, NULL, "Show system status", cmd_status),
    SHELL_CMD(ff, NULL, "Set force feedback mode", cmd_ff),
    SHELL_SUBCMD_SET_END
);
SHELL_CMD_REGISTER(fader, &fader_cmds, "Motor fader commands", NULL);

/*
 * Main entry point
 */
int main(void)
{
    int ret;
    
    LOG_INF("Motor Fader Firmware Starting...");
    LOG_INF("Pin config: IN1=GPIO4, IN2=GPIO5, nSLEEP=GPIO6");
    LOG_INF("           POT=GPIO2, CURRENT=GPIO3, TOUCH=GPIO1");
    
    /* Initialize settings subsystem */
    ret = settings_subsys_init();
    if (ret) {
        LOG_WRN("Settings init failed: %d", ret);
    }
    
    /* Initialize subsystems */
    ret = motor_init();
    if (ret) {
        LOG_ERR("Motor init failed: %d", ret);
        return ret;
    }
    
    ret = adc_init();
    if (ret) {
        LOG_ERR("ADC init failed: %d", ret);
        return ret;
    }
    
    ret = calibration_init();
    if (ret) {
        LOG_WRN("Calibration init failed: %d", ret);
    }
    
    ret = touch_init();
    if (ret) {
        LOG_WRN("Touch init failed: %d", ret);
    }
    
    /* Initialize PID controller */
    pid_init(&pid, &pid_default_config);
    
    /* Start control loop thread */
    k_thread_create(&control_thread_data, control_stack,
                    K_THREAD_STACK_SIZEOF(control_stack),
                    control_loop_thread, NULL, NULL, NULL,
                    5, 0, K_NO_WAIT);
    k_thread_name_set(&control_thread_data, "control_loop");
    
    LOG_INF("Initialization complete!");
    LOG_INF("Commands available via shell:");
    LOG_INF("  fader demo    - Start back-and-forth demo");
    LOG_INF("  fader stop    - Stop motor");
    LOG_INF("  fader cal     - Run calibration");
    LOG_INF("  fader pos <%%> - Set target position");
    LOG_INF("  fader status  - Show current status");
    
    app_state = APP_STATE_IDLE;
    
    /* Main loop - just log status periodically for debugging */
    while (1) {
        k_msleep(5000);
        
        if (app_state != APP_STATE_IDLE) {
            LOG_INF("pos=%.1f%% target=%.1f%% current=%d",
                    current_position * 100.0f,
                    target_position * 100.0f,
                    raw_current_value);
        }
    }
    
    return 0;
}

