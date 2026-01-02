/*
 * Touch Detection and Force Feedback Implementation
 * 
 * Detection methods:
 * 1. Capacitive touch sensing on GPIO1 (TOUCH1)
 * 2. Current-based force detection (backup/supplement)
 * 
 * Force feedback behavior:
 * - When user touches fader, reduce motor torque
 * - If user applies force (detected via current), yield
 * - Option to spring back to target or adopt new position
 */

#include "touch_detect.h"
#include "calibration.h"
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <math.h>

LOG_MODULE_REGISTER(touch_detect, LOG_LEVEL_INF);

/* Touch detection parameters */
#define TOUCH_THRESHOLD_DEFAULT     1000    /* ADC threshold for capacitive touch */
#define TOUCH_DEBOUNCE_MS           20      /* Debounce time */
#define TOUCH_MOVE_THRESHOLD        0.02f   /* Position change to consider "moving" */

/* Force detection parameters */
#define CURRENT_THRESHOLD_DEFAULT   300     /* ADC value ~100mA with 1ohm sense */
#define CURRENT_SAMPLES             3       /* Samples above threshold for detection */

/* Module state */
static touch_state_t touch_state = TOUCH_STATE_IDLE;
static force_feedback_mode_t ff_mode = FF_MODE_HOLD;
static touch_callback_t touch_callback = NULL;

static uint16_t touch_threshold = TOUCH_THRESHOLD_DEFAULT;
static uint16_t current_threshold = CURRENT_THRESHOLD_DEFAULT;

static uint32_t touch_start_time;
static uint32_t release_start_time;
static float touch_start_position;
static float last_position;
static uint8_t current_high_count;

/* Internal helpers */
static void set_state(touch_state_t new_state)
{
    if (touch_state != new_state) {
        LOG_DBG("Touch state: %d -> %d", touch_state, new_state);
        touch_state = new_state;
        
        if (touch_callback) {
            touch_callback(new_state);
        }
    }
}

int touch_init(void)
{
    LOG_INF("Initializing touch detection...");
    
    touch_state = TOUCH_STATE_IDLE;
    ff_mode = FF_MODE_HOLD;
    touch_start_position = 0.0f;
    last_position = 0.0f;
    current_high_count = 0;
    
    /* 
     * Note: ESP32-S3 has hardware touch sensing but Zephyr support
     * may be limited. Using ADC fallback for now.
     * For production, consider implementing direct register access
     * to the touch controller or using ESP-IDF touch driver.
     */
    
    LOG_INF("Touch detection initialized");
    return 0;
}

void touch_process(uint16_t touch_adc, uint16_t current_adc, float position)
{
    bool touch_detected = (touch_adc > touch_threshold);
    bool current_high = (current_adc > current_threshold);
    float position_delta = fabsf(position - last_position);
    
    /* Track consecutive high current samples */
    if (current_high) {
        if (current_high_count < 255) {
            current_high_count++;
        }
    } else {
        current_high_count = 0;
    }
    
    switch (touch_state) {
    case TOUCH_STATE_IDLE:
        if (touch_detected) {
            touch_start_time = k_uptime_get_32();
            touch_start_position = position;
            set_state(TOUCH_STATE_TOUCHED);
            LOG_INF("Touch detected at position %.2f", position);
        }
        break;
        
    case TOUCH_STATE_TOUCHED:
        if (!touch_detected) {
            /* Debounce release */
            release_start_time = k_uptime_get_32();
            set_state(TOUCH_STATE_RELEASED);
        } else if (position_delta > TOUCH_MOVE_THRESHOLD) {
            /* User is moving the fader */
            set_state(TOUCH_STATE_MOVING);
            LOG_INF("User moving fader");
        }
        break;
        
    case TOUCH_STATE_MOVING:
        if (!touch_detected) {
            release_start_time = k_uptime_get_32();
            set_state(TOUCH_STATE_RELEASED);
            LOG_INF("Touch released at position %.2f", position);
        }
        /* Stay in moving state while touched, regardless of movement */
        break;
        
    case TOUCH_STATE_RELEASED:
        if (touch_detected) {
            /* Touch returned before debounce complete */
            set_state(TOUCH_STATE_TOUCHED);
        } else if (k_uptime_get_32() - release_start_time > TOUCH_DEBOUNCE_MS) {
            /* Debounce complete, fully released */
            set_state(TOUCH_STATE_IDLE);
        }
        break;
    }
    
    last_position = position;
}

touch_state_t touch_get_state(void)
{
    return touch_state;
}

bool touch_is_touched(void)
{
    return (touch_state == TOUCH_STATE_TOUCHED || 
            touch_state == TOUCH_STATE_MOVING);
}

bool touch_is_moving(void)
{
    return (touch_state == TOUCH_STATE_MOVING);
}

void touch_set_threshold(uint16_t threshold)
{
    touch_threshold = threshold;
}

void touch_set_ff_mode(force_feedback_mode_t mode)
{
    ff_mode = mode;
    LOG_INF("Force feedback mode: %d", mode);
}

force_feedback_mode_t touch_get_ff_mode(void)
{
    return ff_mode;
}

void touch_register_callback(touch_callback_t callback)
{
    touch_callback = callback;
}

bool touch_should_yield(uint16_t current_adc)
{
    /*
     * Yield to user force when:
     * - Force feedback mode allows it
     * - Current exceeds threshold for multiple samples
     * - User is touching the fader
     */
    
    if (ff_mode == FF_MODE_DISABLED) {
        return false;
    }
    
    if (ff_mode == FF_MODE_FOLLOW) {
        /* Always yield in follow mode */
        return touch_is_touched();
    }
    
    /* In HOLD or SPRING mode, yield only on force */
    return (current_high_count >= CURRENT_SAMPLES);
}

float touch_get_start_position(void)
{
    return touch_start_position;
}

void touch_set_current_threshold(uint16_t threshold)
{
    current_threshold = threshold;
}

