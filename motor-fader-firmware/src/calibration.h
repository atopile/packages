/*
 * Calibration Module
 * 
 * Handles endstop calibration for the motor fader using
 * current sensing and position feedback.
 */

#ifndef CALIBRATION_H
#define CALIBRATION_H

#include <stdint.h>
#include <stdbool.h>

/* Calibration data structure */
typedef struct {
    uint16_t pos_min;       /* ADC value at minimum position */
    uint16_t pos_max;       /* ADC value at maximum position */
    uint16_t current_stall; /* ADC value indicating stall current */
    bool valid;             /* Calibration data is valid */
} calibration_data_t;

/* Calibration state */
typedef enum {
    CAL_STATE_IDLE,
    CAL_STATE_FINDING_MIN,
    CAL_STATE_FINDING_MAX,
    CAL_STATE_COMPLETE,
    CAL_STATE_ERROR
} calibration_state_t;

/**
 * Initialize calibration module
 * @return 0 on success, negative error code on failure
 */
int calibration_init(void);

/**
 * Start automatic calibration procedure
 * This runs asynchronously - use calibration_get_state() to check progress
 * @return 0 on success, negative error code if already running
 */
int calibration_start(void);

/**
 * Get current calibration state
 * @return Current state
 */
calibration_state_t calibration_get_state(void);

/**
 * Process calibration step (call from main loop)
 * @param position Current position ADC value
 * @param current Current sense ADC value
 */
void calibration_process(uint16_t position, uint16_t current);

/**
 * Abort ongoing calibration
 */
void calibration_abort(void);

/**
 * Get calibration data
 * @return Pointer to calibration data (NULL if not valid)
 */
const calibration_data_t* calibration_get_data(void);

/**
 * Set calibration data manually
 * @param data Pointer to calibration data
 * @return 0 on success
 */
int calibration_set_data(const calibration_data_t *data);

/**
 * Save calibration data to NVS
 * @return 0 on success
 */
int calibration_save(void);

/**
 * Load calibration data from NVS
 * @return 0 on success, negative if no data or invalid
 */
int calibration_load(void);

/**
 * Convert raw ADC position to normalized 0.0-1.0 range
 * @param raw_position Raw ADC value
 * @return Normalized position (0.0 to 1.0)
 */
float calibration_normalize_position(uint16_t raw_position);

/**
 * Convert normalized position to raw ADC value
 * @param normalized Normalized position (0.0 to 1.0)
 * @return Raw ADC value
 */
uint16_t calibration_denormalize_position(float normalized);

#endif /* CALIBRATION_H */

