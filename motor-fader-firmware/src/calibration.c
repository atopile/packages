/*
 * Calibration Module Implementation
 * 
 * Endstop calibration procedure:
 * 1. Drive motor slowly toward minimum position
 * 2. Detect stall via current spike
 * 3. Record minimum position ADC value
 * 4. Drive motor toward maximum position
 * 5. Detect stall, record maximum position
 * 6. Store calibration in NVS
 */

#include "calibration.h"
#include "motor_control.h"
#include <zephyr/kernel.h>
#include <zephyr/settings/settings.h>
#include <zephyr/logging/log.h>
#include <string.h>

LOG_MODULE_REGISTER(calibration, LOG_LEVEL_INF);

/* Calibration parameters */
#define CAL_MOTOR_SPEED       30      /* Slow speed during calibration (%) */
#define CAL_STALL_THRESHOLD   500     /* ADC value indicating stall (~150mA @ 1ohm, 3.3V ref) */
#define CAL_STALL_SAMPLES     5       /* Consecutive samples above threshold to confirm stall */
#define CAL_SETTLE_TIME_MS    100     /* Time to wait after stopping */
#define CAL_TIMEOUT_MS        5000    /* Max time for each direction */

/* NVS settings key */
#define CAL_SETTINGS_KEY      "motor_fader/cal"

/* Module state */
static calibration_data_t cal_data = {
    .pos_min = 0,
    .pos_max = 4095,
    .current_stall = CAL_STALL_THRESHOLD,
    .valid = false
};

static calibration_state_t cal_state = CAL_STATE_IDLE;
static uint32_t cal_start_time;
static uint8_t stall_count;
static uint16_t last_position;

/* Settings handler for NVS */
static int cal_settings_set(const char *name, size_t len,
                            settings_read_cb read_cb, void *cb_arg)
{
    const char *next;
    
    if (settings_name_steq(name, "data", &next) && !next) {
        if (len != sizeof(calibration_data_t)) {
            return -EINVAL;
        }
        
        int rc = read_cb(cb_arg, &cal_data, sizeof(cal_data));
        if (rc >= 0) {
            LOG_INF("Loaded calibration: min=%d, max=%d", 
                    cal_data.pos_min, cal_data.pos_max);
            return 0;
        }
        return rc;
    }
    
    return -ENOENT;
}

static int cal_settings_export(int (*cb)(const char *name, const void *value,
                                         size_t val_len))
{
    if (cal_data.valid) {
        return cb(CAL_SETTINGS_KEY "/data", &cal_data, sizeof(cal_data));
    }
    return 0;
}

SETTINGS_STATIC_HANDLER_DEFINE(motor_fader_cal, CAL_SETTINGS_KEY,
                               NULL, cal_settings_set, NULL, 
                               cal_settings_export);

int calibration_init(void)
{
    LOG_INF("Initializing calibration module...");
    
    /* Try to load existing calibration */
    if (calibration_load() == 0) {
        LOG_INF("Loaded existing calibration data");
    } else {
        LOG_INF("No valid calibration data, using defaults");
    }
    
    return 0;
}

int calibration_start(void)
{
    if (cal_state != CAL_STATE_IDLE && cal_state != CAL_STATE_COMPLETE &&
        cal_state != CAL_STATE_ERROR) {
        LOG_WRN("Calibration already in progress");
        return -EBUSY;
    }
    
    LOG_INF("Starting calibration...");
    
    /* Reset state */
    cal_state = CAL_STATE_FINDING_MIN;
    cal_start_time = k_uptime_get_32();
    stall_count = 0;
    
    /* Make sure motor is enabled */
    motor_enable(true);
    
    /* Start moving toward minimum */
    motor_set(MOTOR_DIR_REVERSE, CAL_MOTOR_SPEED);
    
    return 0;
}

calibration_state_t calibration_get_state(void)
{
    return cal_state;
}

void calibration_process(uint16_t position, uint16_t current)
{
    uint32_t elapsed;
    
    switch (cal_state) {
    case CAL_STATE_IDLE:
    case CAL_STATE_COMPLETE:
    case CAL_STATE_ERROR:
        /* Nothing to do */
        return;
        
    case CAL_STATE_FINDING_MIN:
        elapsed = k_uptime_get_32() - cal_start_time;
        
        /* Check for timeout */
        if (elapsed > CAL_TIMEOUT_MS) {
            LOG_ERR("Calibration timeout finding minimum");
            motor_stop();
            cal_state = CAL_STATE_ERROR;
            return;
        }
        
        /* Check for stall */
        if (current > cal_data.current_stall) {
            stall_count++;
            if (stall_count >= CAL_STALL_SAMPLES) {
                /* Stall detected - found minimum */
                motor_stop();
                k_msleep(CAL_SETTLE_TIME_MS);
                
                cal_data.pos_min = position;
                LOG_INF("Found minimum position: %d", cal_data.pos_min);
                
                /* Start finding maximum */
                stall_count = 0;
                cal_start_time = k_uptime_get_32();
                cal_state = CAL_STATE_FINDING_MAX;
                
                motor_set(MOTOR_DIR_FORWARD, CAL_MOTOR_SPEED);
            }
        } else {
            stall_count = 0;
        }
        break;
        
    case CAL_STATE_FINDING_MAX:
        elapsed = k_uptime_get_32() - cal_start_time;
        
        /* Check for timeout */
        if (elapsed > CAL_TIMEOUT_MS) {
            LOG_ERR("Calibration timeout finding maximum");
            motor_stop();
            cal_state = CAL_STATE_ERROR;
            return;
        }
        
        /* Check for stall */
        if (current > cal_data.current_stall) {
            stall_count++;
            if (stall_count >= CAL_STALL_SAMPLES) {
                /* Stall detected - found maximum */
                motor_stop();
                k_msleep(CAL_SETTLE_TIME_MS);
                
                cal_data.pos_max = position;
                cal_data.valid = true;
                cal_state = CAL_STATE_COMPLETE;
                
                LOG_INF("Found maximum position: %d", cal_data.pos_max);
                LOG_INF("Calibration complete: range = %d to %d",
                        cal_data.pos_min, cal_data.pos_max);
                
                /* Auto-save */
                calibration_save();
            }
        } else {
            stall_count = 0;
        }
        break;
    }
    
    last_position = position;
}

void calibration_abort(void)
{
    if (cal_state == CAL_STATE_FINDING_MIN || 
        cal_state == CAL_STATE_FINDING_MAX) {
        LOG_WRN("Aborting calibration");
        motor_stop();
        cal_state = CAL_STATE_IDLE;
    }
}

const calibration_data_t* calibration_get_data(void)
{
    if (cal_data.valid) {
        return &cal_data;
    }
    return NULL;
}

int calibration_set_data(const calibration_data_t *data)
{
    if (!data) {
        return -EINVAL;
    }
    
    memcpy(&cal_data, data, sizeof(cal_data));
    return 0;
}

int calibration_save(void)
{
    if (!cal_data.valid) {
        LOG_WRN("Cannot save invalid calibration data");
        return -EINVAL;
    }
    
    int ret = settings_save_one(CAL_SETTINGS_KEY "/data", 
                                &cal_data, sizeof(cal_data));
    if (ret) {
        LOG_ERR("Failed to save calibration: %d", ret);
    } else {
        LOG_INF("Calibration saved");
    }
    
    return ret;
}

int calibration_load(void)
{
    int ret = settings_load_subtree(CAL_SETTINGS_KEY);
    if (ret) {
        LOG_WRN("Failed to load calibration settings: %d", ret);
        return ret;
    }
    
    if (!cal_data.valid) {
        return -ENOENT;
    }
    
    return 0;
}

float calibration_normalize_position(uint16_t raw_position)
{
    if (!cal_data.valid) {
        /* Default: assume 12-bit ADC, 0-4095 */
        return (float)raw_position / 4095.0f;
    }
    
    /* Normalize to 0.0 - 1.0 based on calibration */
    int32_t range = (int32_t)cal_data.pos_max - (int32_t)cal_data.pos_min;
    if (range <= 0) {
        return 0.5f;  /* Invalid range */
    }
    
    int32_t offset = (int32_t)raw_position - (int32_t)cal_data.pos_min;
    float normalized = (float)offset / (float)range;
    
    /* Clamp to 0.0 - 1.0 */
    if (normalized < 0.0f) normalized = 0.0f;
    if (normalized > 1.0f) normalized = 1.0f;
    
    return normalized;
}

uint16_t calibration_denormalize_position(float normalized)
{
    /* Clamp input */
    if (normalized < 0.0f) normalized = 0.0f;
    if (normalized > 1.0f) normalized = 1.0f;
    
    if (!cal_data.valid) {
        /* Default: assume 12-bit ADC */
        return (uint16_t)(normalized * 4095.0f);
    }
    
    int32_t range = (int32_t)cal_data.pos_max - (int32_t)cal_data.pos_min;
    int32_t raw = (int32_t)cal_data.pos_min + (int32_t)(normalized * (float)range);
    
    return (uint16_t)raw;
}

