/*
 * Motor Control Module Implementation
 * 
 * DRV8210P H-bridge control using ESP32-S3 LEDC PWM
 * 
 * Pin Assignments:
 *   GPIO4 - IN1 (PWM)
 *   GPIO5 - IN2 (PWM)
 *   GPIO6 - nSLEEP (active high to enable)
 * 
 * Control Logic:
 *   IN1=H, IN2=L -> Forward
 *   IN1=L, IN2=H -> Reverse
 *   IN1=L, IN2=L -> Coast (stop)
 *   IN1=H, IN2=H -> Brake
 */

#include "motor_control.h"
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/pwm.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(motor_control, LOG_LEVEL_INF);

/* GPIO pin definitions */
#define MOTOR_IN1_PIN   4
#define MOTOR_IN2_PIN   5
#define MOTOR_SLEEP_PIN 6

/* PWM parameters */
#define PWM_PERIOD_NS   50000  /* 20kHz = 50us period */
#define PWM_MAX_DUTY    PWM_PERIOD_NS

/* Device handles */
static const struct device *gpio_dev;
static const struct device *pwm_dev;

/* Current motor state */
static motor_state_t motor_state = {
    .enabled = false,
    .direction = MOTOR_DIR_STOP,
    .speed = 0,
    .pwm_value = 0
};

int motor_init(void)
{
    int ret;

    LOG_INF("Initializing motor control...");

    /* Get GPIO device */
    gpio_dev = DEVICE_DT_GET(DT_NODELABEL(gpio0));
    if (!device_is_ready(gpio_dev)) {
        LOG_ERR("GPIO device not ready");
        return -ENODEV;
    }

    /* Configure nSLEEP pin as output, initially low (sleep mode) */
    ret = gpio_pin_configure(gpio_dev, MOTOR_SLEEP_PIN, GPIO_OUTPUT_LOW);
    if (ret < 0) {
        LOG_ERR("Failed to configure nSLEEP pin: %d", ret);
        return ret;
    }

    /* Get PWM device - using LEDC */
    pwm_dev = DEVICE_DT_GET(DT_NODELABEL(ledc0));
    if (!device_is_ready(pwm_dev)) {
        LOG_WRN("PWM device not ready, falling back to GPIO mode");
        
        /* Configure IN1 and IN2 as GPIO outputs for basic control */
        ret = gpio_pin_configure(gpio_dev, MOTOR_IN1_PIN, GPIO_OUTPUT_LOW);
        if (ret < 0) {
            LOG_ERR("Failed to configure IN1 pin: %d", ret);
            return ret;
        }
        
        ret = gpio_pin_configure(gpio_dev, MOTOR_IN2_PIN, GPIO_OUTPUT_LOW);
        if (ret < 0) {
            LOG_ERR("Failed to configure IN2 pin: %d", ret);
            return ret;
        }
        
        pwm_dev = NULL;
    }

    LOG_INF("Motor control initialized");
    return 0;
}

void motor_enable(bool enable)
{
    if (gpio_dev) {
        gpio_pin_set(gpio_dev, MOTOR_SLEEP_PIN, enable ? 1 : 0);
        motor_state.enabled = enable;
        
        if (!enable) {
            motor_state.direction = MOTOR_DIR_STOP;
            motor_state.speed = 0;
        }
        
        LOG_INF("Motor driver %s", enable ? "enabled" : "disabled");
    }
}

bool motor_is_enabled(void)
{
    return motor_state.enabled;
}

static void set_pwm_outputs(uint32_t in1_duty, uint32_t in2_duty)
{
    if (pwm_dev) {
        /* Use PWM for smooth control */
        pwm_set(pwm_dev, 0, PWM_PERIOD_NS, in1_duty, 0);
        pwm_set(pwm_dev, 1, PWM_PERIOD_NS, in2_duty, 0);
    } else if (gpio_dev) {
        /* Fallback to GPIO - no speed control, just on/off */
        gpio_pin_set(gpio_dev, MOTOR_IN1_PIN, in1_duty > 0 ? 1 : 0);
        gpio_pin_set(gpio_dev, MOTOR_IN2_PIN, in2_duty > 0 ? 1 : 0);
    }
}

void motor_set(motor_direction_t direction, uint8_t speed)
{
    if (!motor_state.enabled) {
        LOG_WRN("Motor driver not enabled");
        return;
    }

    /* Clamp speed to 0-100 */
    if (speed > 100) {
        speed = 100;
    }

    uint32_t duty = (uint32_t)speed * PWM_MAX_DUTY / 100;

    motor_state.direction = direction;
    motor_state.speed = speed;

    switch (direction) {
    case MOTOR_DIR_FORWARD:
        set_pwm_outputs(duty, 0);
        motor_state.pwm_value = (int16_t)speed;
        LOG_DBG("Motor forward, speed=%d%%", speed);
        break;

    case MOTOR_DIR_REVERSE:
        set_pwm_outputs(0, duty);
        motor_state.pwm_value = -(int16_t)speed;
        LOG_DBG("Motor reverse, speed=%d%%", speed);
        break;

    case MOTOR_DIR_BRAKE:
        set_pwm_outputs(PWM_MAX_DUTY, PWM_MAX_DUTY);
        motor_state.pwm_value = 0;
        LOG_DBG("Motor brake");
        break;

    case MOTOR_DIR_STOP:
    default:
        set_pwm_outputs(0, 0);
        motor_state.pwm_value = 0;
        LOG_DBG("Motor stop");
        break;
    }
}

void motor_set_output(int8_t value)
{
    if (value > 0) {
        motor_set(MOTOR_DIR_FORWARD, (uint8_t)value);
    } else if (value < 0) {
        motor_set(MOTOR_DIR_REVERSE, (uint8_t)(-value));
    } else {
        motor_set(MOTOR_DIR_STOP, 0);
    }
}

void motor_stop(void)
{
    motor_set(MOTOR_DIR_STOP, 0);
}

void motor_brake(void)
{
    motor_set(MOTOR_DIR_BRAKE, 0);
}

const motor_state_t* motor_get_state(void)
{
    return &motor_state;
}

