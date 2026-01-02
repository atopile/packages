/*
 * Touch Detection and Force Feedback Module
 * 
 * Handles capacitive touch sensing and force feedback
 * to allow user override of motor position.
 */

#ifndef TOUCH_DETECT_H
#define TOUCH_DETECT_H

#include <stdint.h>
#include <stdbool.h>

/* Touch state */
typedef enum {
    TOUCH_STATE_IDLE,       /* No touch detected */
    TOUCH_STATE_TOUCHED,    /* User is touching fader */
    TOUCH_STATE_MOVING,     /* User is actively moving fader */
    TOUCH_STATE_RELEASED    /* Just released (debounce) */
} touch_state_t;

/* Force feedback mode */
typedef enum {
    FF_MODE_DISABLED,       /* No force feedback */
    FF_MODE_HOLD,           /* Hold position, yield to user force */
    FF_MODE_SPRING,         /* Spring back to target after release */
    FF_MODE_FOLLOW          /* Follow user movement, no motor force */
} force_feedback_mode_t;

/* Touch callback type */
typedef void (*touch_callback_t)(touch_state_t state);

/**
 * Initialize touch detection module
 * @return 0 on success, negative error code on failure
 */
int touch_init(void);

/**
 * Process touch detection (call from main loop)
 * @param touch_adc Raw ADC value from touch pin (or GPIO state)
 * @param current_adc Current sense ADC value
 * @param position Current position (normalized 0.0-1.0)
 */
void touch_process(uint16_t touch_adc, uint16_t current_adc, float position);

/**
 * Get current touch state
 * @return Current touch state
 */
touch_state_t touch_get_state(void);

/**
 * Check if user is touching the fader
 * @return true if touching
 */
bool touch_is_touched(void);

/**
 * Check if user is actively moving the fader
 * @return true if moving
 */
bool touch_is_moving(void);

/**
 * Set touch detection threshold
 * @param threshold ADC threshold for touch detection
 */
void touch_set_threshold(uint16_t threshold);

/**
 * Set force feedback mode
 * @param mode Force feedback mode
 */
void touch_set_ff_mode(force_feedback_mode_t mode);

/**
 * Get force feedback mode
 * @return Current mode
 */
force_feedback_mode_t touch_get_ff_mode(void);

/**
 * Register callback for touch state changes
 * @param callback Callback function (can be NULL to unregister)
 */
void touch_register_callback(touch_callback_t callback);

/**
 * Check if motor should yield to user (based on current sensing)
 * @param current_adc Current sense ADC value
 * @return true if excessive current detected (user pushing)
 */
bool touch_should_yield(uint16_t current_adc);

/**
 * Get the position when user started touching
 * @return Touch start position (normalized)
 */
float touch_get_start_position(void);

/**
 * Set current threshold for force detection
 * @param threshold Current ADC threshold
 */
void touch_set_current_threshold(uint16_t threshold);

#endif /* TOUCH_DETECT_H */

