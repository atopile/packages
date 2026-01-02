/*
 * Motor Fader Firmware - Arduino/ESP32 Version
 *
 * ESP32-S3 + DRV8210P H-bridge + ALPS Motor Fader
 *
 * This is a simplified Arduino version for rapid prototyping.
 * For production, consider the Zephyr RTOS version.
 *
 * Pin Assignments (from usage.ato):
 *   GPIO4  - Motor IN1 (PWM)
 *   GPIO5  - Motor IN2 (PWM)
 *   GPIO6  - Driver nSLEEP (active high)
 *   GPIO2  - Potentiometer sense (ADC)
 *   GPIO3  - Current sense (ADC)
 *   GPIO1  - Touch sense
 */

#include <Arduino.h>

// Pin definitions
// Motor: in_1~io[4], in_2~io[5], sleep~io[6]
// Sensors: EMPIRICALLY VERIFIED - GPIO1 is pot (ADC scan shows it changes with fader)
#define PIN_MOTOR_IN1 4
#define PIN_MOTOR_IN2 5
#define PIN_MOTOR_SLEEP 6
#define PIN_POT_SENSE 2     // GPIO2 - verified by hardware measurement
#define PIN_CURRENT_SENSE 3 // GPIO3
#define PIN_TOUCH_SENSE 1   // GPIO1

// PWM configuration
#define PWM_FREQ 20000   // 20kHz for silent operation
#define PWM_RESOLUTION 8 // 8-bit resolution (0-255)
#define PWM_CHANNEL_IN1 0
#define PWM_CHANNEL_IN2 1

// Control parameters
#define CONTROL_LOOP_HZ 2000 // 2kHz control loop for pro-grade response
#define ADC_SAMPLES 2        // Minimal for 2kHz loop

// Smooth motion tuning
float Kp = 800.0f; // Proportional
float Ki = 0.0f;   // No integral
float Kd = 0.0f;   // Small derivative for damping

// Minimum PWM to overcome static friction
#define MIN_PWM_THRESHOLD 30 // Very low for smooth tracking

// Deadband - don't move if within this percentage of target
#define POSITION_DEADBAND 0.015f // 1.5% for smooth settling

// PID state
float pid_integral = 0.0f;
float pid_prev_error = 0.0f;
float pid_prev_input = 0.0f;
float pid_filtered_derivative = 0.0f; // Low-pass filtered derivative
#define DERIVATIVE_FILTER_ALPHA 0.1f  // 0.0-1.0, lower = more smoothing

// Position tracking
float target_position = 0.5f; // 0.0 to 1.0
float current_position = 0.5f;
uint16_t raw_pot = 0;
uint16_t raw_current = 0;

// Calibration
uint16_t cal_min = 200;        // Default min ADC value
uint16_t cal_max = 3900;       // Default max ADC value
uint16_t current_stall = 1500; // Stall current threshold (increased)
bool calibrated = false;

// State machine
enum AppState
{
    STATE_IDLE,
    STATE_DEMO,
    STATE_POSITION,
    STATE_CALIBRATING_MIN,
    STATE_CALIBRATING_MAX,
    STATE_MANUAL,
    STATE_TOUCH_OVERRIDE, // User is touching fader, follow their input
    STATE_SMOOTH_MOVE,    // Smooth ramping to target
    STATE_SINE_WAVE       // Continuous sine wave motion
};

AppState app_state = STATE_IDLE;
AppState state_before_touch = STATE_IDLE; // State to return to after touch release

// Demo mode
bool demo_direction = true;
unsigned long demo_last_change = 0;
#define DEMO_INTERVAL_MS 3000

// Smooth motion
float smooth_target = 0.5f; // Final target for smooth move
float smooth_rate = 0.002f; // Position change per control loop (0.2% per ms at 1kHz)

// Built-in demo sequence
enum DemoPhase
{
    DEMO_IDLE,
    DEMO_FULLSPEED_UP,
    DEMO_FULLSPEED_DOWN,
    DEMO_STEP,
    DEMO_SMOOTH_UP,
    DEMO_SMOOTH_DOWN,
    DEMO_SINE,
    DEMO_DONE
};
DemoPhase demo_phase = DEMO_IDLE;
unsigned long demo_phase_start = 0;
int demo_cycle_count = 0;
int demo_step_index = 0;
float demo_smooth_pos = 0.1f;

// Touch state
bool is_touched = false;
bool was_touched = false; // Previous touch state for edge detection
bool force_detected = false;
// ESP32-S3 touchRead: ~64000 untouched, ~4000-7000 touched
#define TOUCH_THRESHOLD 30000 // Values below this = touched
#define TOUCH_DEBOUNCE_MS 30  // Debounce time
unsigned long touch_start_time = 0;
unsigned long touch_release_time = 0;

// Timing
unsigned long last_control_time = 0;
#define CONTROL_PERIOD_US (1000000 / CONTROL_LOOP_HZ)

// ============================================================================
// Motor Control
// ============================================================================

void motor_init()
{
    Serial.printf("Motor pins: IN1=GPIO%d, IN2=GPIO%d, SLEEP=GPIO%d\n",
                  PIN_MOTOR_IN1, PIN_MOTOR_IN2, PIN_MOTOR_SLEEP);

    // Configure PWM channels for motor control
    ledcSetup(PWM_CHANNEL_IN1, PWM_FREQ, PWM_RESOLUTION);
    ledcSetup(PWM_CHANNEL_IN2, PWM_FREQ, PWM_RESOLUTION);
    ledcAttachPin(PIN_MOTOR_IN1, PWM_CHANNEL_IN1);
    ledcAttachPin(PIN_MOTOR_IN2, PWM_CHANNEL_IN2);
    ledcWrite(PWM_CHANNEL_IN1, 0);
    ledcWrite(PWM_CHANNEL_IN2, 0);

    // Configure sleep pin - set HIGH to enable driver
    pinMode(PIN_MOTOR_SLEEP, OUTPUT);
    digitalWrite(PIN_MOTOR_SLEEP, HIGH); // Enable driver by default

    Serial.println("Motor initialized (PWM mode) and enabled");
}

void motor_enable(bool enable)
{
    Serial.printf("Motor enable: %s\n", enable ? "ON" : "OFF");
    digitalWrite(PIN_MOTOR_SLEEP, enable ? HIGH : LOW);
    if (!enable)
    {
        ledcWrite(PWM_CHANNEL_IN1, 0);
        ledcWrite(PWM_CHANNEL_IN2, 0);
    }
}

// Set motor output: -255 to +255
// Uses PWM for variable speed control
void motor_set(int16_t value)
{
    value = constrain(value, -255, 255);

    // PWM control - IN2 for UP, IN1 for DOWN (empirically verified)
    if (value > 0)
    {
        // Forward (fader up) - IN2 gets PWM
        ledcWrite(PWM_CHANNEL_IN1, 0);
        ledcWrite(PWM_CHANNEL_IN2, value);
    }
    else if (value < 0)
    {
        // Reverse (fader down) - IN1 gets PWM
        ledcWrite(PWM_CHANNEL_IN1, -value);
        ledcWrite(PWM_CHANNEL_IN2, 0);
    }
    else
    {
        // Stop (coast)
        ledcWrite(PWM_CHANNEL_IN1, 0);
        ledcWrite(PWM_CHANNEL_IN2, 0);
    }
}

void motor_brake()
{
    ledcWrite(PWM_CHANNEL_IN1, 255);
    ledcWrite(PWM_CHANNEL_IN2, 255);
}

// ============================================================================
// ADC Reading with oversampling
// ============================================================================

uint16_t read_adc_averaged(uint8_t pin)
{
    uint32_t sum = 0;
    for (int i = 0; i < ADC_SAMPLES; i++)
    {
        sum += analogRead(pin);
    }
    return sum / ADC_SAMPLES;
}

void read_sensors()
{
    raw_pot = read_adc_averaged(PIN_POT_SENSE);
    raw_current = read_adc_averaged(PIN_CURRENT_SENSE);

    // Normalize position
    if (cal_max > cal_min)
    {
        int32_t range = cal_max - cal_min;
        int32_t offset = raw_pot - cal_min;
        current_position = constrain((float)offset / (float)range, 0.0f, 1.0f);
    }

    // Touch detection with debouncing
    uint16_t touch_val = touchRead(PIN_TOUCH_SENSE);
    bool touch_raw = (touch_val < TOUCH_THRESHOLD);

    // Debounce touch input
    if (touch_raw && !was_touched)
    {
        // Rising edge - start debounce timer
        if (touch_start_time == 0)
        {
            touch_start_time = millis();
        }
        else if (millis() - touch_start_time > TOUCH_DEBOUNCE_MS)
        {
            is_touched = true;
            touch_release_time = 0;
        }
    }
    else if (!touch_raw && was_touched)
    {
        // Falling edge - start release debounce
        if (touch_release_time == 0)
        {
            touch_release_time = millis();
        }
        else if (millis() - touch_release_time > TOUCH_DEBOUNCE_MS)
        {
            is_touched = false;
            touch_start_time = 0;
        }
    }
    else if (touch_raw)
    {
        touch_release_time = 0; // Reset release timer while touched
    }
    else
    {
        touch_start_time = 0; // Reset touch timer while not touched
    }

    was_touched = is_touched;

    // Force detection (high current while holding position)
    force_detected = (raw_current > current_stall / 2);
}

// ============================================================================
// PID Controller
// ============================================================================

float pid_compute(float setpoint, float input, float dt)
{
    float error = setpoint - input;

    // Deadband
    if (abs(error) < POSITION_DEADBAND)
    {
        pid_integral = 0; // Reset integral in deadband
        return 0.0f;
    }

    // Proportional
    float p_term = Kp * error;

    // Integral with anti-windup
    pid_integral += error * dt;
    pid_integral = constrain(pid_integral, -50.0f, 50.0f);
    float i_term = Ki * pid_integral;

    // Derivative (on measurement to avoid kick) with low-pass filter
    float d_input_raw = (input - pid_prev_input) / dt;
    pid_filtered_derivative = DERIVATIVE_FILTER_ALPHA * d_input_raw +
                              (1.0f - DERIVATIVE_FILTER_ALPHA) * pid_filtered_derivative;
    float d_term = -Kd * pid_filtered_derivative;

    pid_prev_error = error;
    pid_prev_input = input;

    // Output
    float output = p_term + i_term + d_term;
    return constrain(output, -100.0f, 100.0f);
}

void pid_reset()
{
    pid_integral = 0.0f;
    pid_prev_error = 0.0f;
    pid_prev_input = current_position;
    pid_filtered_derivative = 0.0f;
}

// ============================================================================
// Calibration
// ============================================================================

// Calibration state
static uint16_t cal_last_pos = 0;
static uint8_t cal_stall_count = 0;
static unsigned long cal_start_time = 0;
static unsigned long cal_move_start = 0;
#define CAL_MOTOR_SPEED 180      // PWM for calibration movement (strong enough to move)
#define CAL_STALL_THRESHOLD 20   // Consecutive readings to confirm stall
#define CAL_POSITION_TOLERANCE 3 // ADC counts - if position doesn't change, we're stalled
#define CAL_TIMEOUT_MS 8000      // Timeout for each direction
#define CAL_SETTLE_MS 500        // Wait before checking for stall (let motor get moving)

void calibration_start()
{
    Serial.println("\n=== Starting Calibration ===");
    Serial.println("Finding minimum position...");
    motor_enable(true);
    app_state = STATE_CALIBRATING_MIN;
    cal_stall_count = 0;
    cal_last_pos = raw_pot;
    cal_start_time = millis();
    cal_move_start = millis();
    motor_set(-CAL_MOTOR_SPEED); // Move toward minimum
}

bool calibration_check_stall()
{
    // Don't check for stall until motor has had time to start moving
    if (millis() - cal_move_start < CAL_SETTLE_MS)
    {
        cal_last_pos = raw_pot; // Keep updating reference position
        return false;
    }

    // Position-based stall detection
    int pos_delta = abs((int)raw_pot - (int)cal_last_pos);
    if (pos_delta < CAL_POSITION_TOLERANCE)
    {
        cal_stall_count++;
    }
    else
    {
        cal_stall_count = 0;
        cal_last_pos = raw_pot;
    }

    return (cal_stall_count > CAL_STALL_THRESHOLD);
}

void calibration_process()
{
    // Check timeout
    if (millis() - cal_start_time > CAL_TIMEOUT_MS)
    {
        motor_set(0);
        Serial.println("Calibration timeout!");
        app_state = STATE_IDLE;
        return;
    }

    if (app_state == STATE_CALIBRATING_MIN)
    {
        if (calibration_check_stall())
        {
            motor_set(0);
            delay(200);
            read_sensors(); // Get fresh reading
            cal_min = raw_pot;
            Serial.printf("Found minimum: %d (ADC)\n", cal_min);

            Serial.println("Finding maximum position...");
            app_state = STATE_CALIBRATING_MAX;
            cal_stall_count = 0;
            cal_last_pos = raw_pot;
            cal_start_time = millis();
            cal_move_start = millis(); // Reset settle timer
            delay(200);
            motor_set(CAL_MOTOR_SPEED); // Move toward maximum
        }
    }
    else if (app_state == STATE_CALIBRATING_MAX)
    {
        if (calibration_check_stall())
        {
            motor_set(0);
            delay(100);
            read_sensors(); // Get fresh reading
            cal_max = raw_pot;
            Serial.printf("Found maximum: %d (ADC)\n", cal_max);

            // Validate calibration
            if (cal_max > cal_min + 100) // At least 100 ADC counts range
            {
                calibrated = true;
                Serial.println("\n=== Calibration Complete ===");
                Serial.printf("Range: %d to %d (%d counts)\n", cal_min, cal_max, cal_max - cal_min);
                Serial.printf("Travel: %.1f%% of ADC range\n", (cal_max - cal_min) / 40.95f);
            }
            else
            {
                Serial.println("ERROR: Calibration failed - range too small!");
                Serial.println("Check motor connections and try again.");
            }

            app_state = STATE_IDLE;
            motor_enable(false);
        }
    }
}

// ============================================================================
// Demo Mode - Full showcase sequence
// ============================================================================

void demo_start()
{
    Serial.println("\n========================================");
    Serial.println("   MOTOR FADER DEMO SEQUENCE");
    Serial.println("========================================\n");
    motor_enable(true);
    pid_reset();
    demo_phase = DEMO_FULLSPEED_UP;
    demo_phase_start = millis();
    demo_cycle_count = 0;
    demo_step_index = 0;
    demo_smooth_pos = 0.05f;
    target_position = 0.95f;
    Serial.println("Phase 1: FULL SPEED SWEEPS (5x)");
}

void demo_update()
{
    unsigned long now = millis();
    unsigned long phase_time = now - demo_phase_start;

    switch (demo_phase)
    {
    // ---- Phase 1: Full speed sweeps ----
    case DEMO_FULLSPEED_UP:
        target_position = 0.95f;
        if (current_position > 0.90f || phase_time > 500)
        {
            demo_phase = DEMO_FULLSPEED_DOWN;
            demo_phase_start = now;
        }
        break;

    case DEMO_FULLSPEED_DOWN:
        target_position = 0.05f;
        if (current_position < 0.10f || phase_time > 500)
        {
            demo_cycle_count++;
            if (demo_cycle_count >= 5)
            {
                Serial.println("\nPhase 2: STEP POSITIONING");
                demo_phase = DEMO_STEP;
                demo_step_index = 0;
                demo_phase_start = now;
            }
            else
            {
                demo_phase = DEMO_FULLSPEED_UP;
                demo_phase_start = now;
            }
        }
        break;

    // ---- Phase 2: Step positioning ----
    case DEMO_STEP:
    {
        static const float step_positions[] = {0.0f, 0.25f, 0.50f, 0.75f, 1.0f, 0.66f, 0.33f, 0.50f};
        static const int num_steps = 8;

        target_position = step_positions[demo_step_index];

        // Wait for position or timeout
        if (abs(current_position - target_position) < 0.03f || phase_time > 800)
        {
            demo_step_index++;
            demo_phase_start = now;

            if (demo_step_index >= num_steps)
            {
                Serial.println("\nPhase 3: SMOOTH SLOW MOTION");
                demo_phase = DEMO_SMOOTH_UP;
                demo_smooth_pos = 0.05f;
                target_position = demo_smooth_pos;
            }
        }
    }
    break;

    // ---- Phase 3: Smooth motion ----
    case DEMO_SMOOTH_UP:
        // Gradually increase target (0.1% per loop = 100% per second at 1kHz)
        demo_smooth_pos += 0.0005f; // 0.05% per loop = smooth crawl
        target_position = demo_smooth_pos;

        if (demo_smooth_pos >= 0.95f)
        {
            demo_phase = DEMO_SMOOTH_DOWN;
        }
        break;

    case DEMO_SMOOTH_DOWN:
        demo_smooth_pos -= 0.0005f;
        target_position = demo_smooth_pos;

        if (demo_smooth_pos <= 0.05f)
        {
            Serial.println("\nPhase 4: SINE WAVE MOTION");
            demo_phase = DEMO_SINE;
            demo_phase_start = now;
            demo_cycle_count = 0;
        }
        break;

    // ---- Phase 4: Sine wave ----
    case DEMO_SINE:
    {
        // Sine wave: 0.25Hz (slow), amplitude 40% (10% to 90%)
        float t = (float)phase_time / 1000.0f; // Time in seconds
        target_position = 0.5f + 0.4f * sin(2.0f * 3.14159f * 0.25f * t);

        // Run for 8 seconds (2 full cycles at 0.25Hz)
        if (phase_time > 8000)
        {
            demo_phase = DEMO_DONE;
            demo_phase_start = now;
        }
    }
    break;

    case DEMO_DONE:
        target_position = 0.5f; // Return to center
        if (phase_time > 1000)
        {
            Serial.println("\n--- Restarting demo loop ---\n");
            // Loop back to start
            demo_phase = DEMO_FULLSPEED_UP;
            demo_phase_start = millis();
            demo_cycle_count = 0;
            demo_step_index = 0;
            demo_smooth_pos = 0.05f;
            target_position = 0.95f;
            Serial.println("Phase 1: FULL SPEED SWEEPS (5x)");
        }
        break;

    default:
        break;
    }
}

// ============================================================================
// Serial Commands
// ============================================================================

void process_serial()
{
    if (!Serial.available())
        return;

    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "demo")
    {
        app_state = STATE_DEMO;
        demo_start();
    }
    else if (cmd == "stop")
    {
        Serial.println("Stopping motor");
        motor_set(0);
        motor_enable(false);
        app_state = STATE_IDLE;
    }
    else if (cmd == "cal")
    {
        calibration_start();
    }
    else if (cmd.startsWith("pos "))
    {
        float pos = cmd.substring(4).toFloat();
        target_position = constrain(pos / 100.0f, 0.0f, 1.0f);
        Serial.printf("Target position: %.1f%%\n", target_position * 100);
        if (app_state == STATE_IDLE)
        {
            motor_enable(true);
            pid_reset();
            app_state = STATE_POSITION;
        }
    }
    else if (cmd.startsWith("motor "))
    {
        int value = cmd.substring(6).toInt();
        Serial.printf("Manual motor: %d\n", value);
        motor_enable(true);
        motor_set(value);
        app_state = STATE_MANUAL;
    }
    else if (cmd.startsWith("pid "))
    {
        // Parse "pid Kp Ki Kd"
        int space1 = cmd.indexOf(' ', 4);
        int space2 = cmd.indexOf(' ', space1 + 1);
        if (space1 > 0 && space2 > 0)
        {
            Kp = cmd.substring(4, space1).toFloat();
            Ki = cmd.substring(space1 + 1, space2).toFloat();
            Kd = cmd.substring(space2 + 1).toFloat();
            Serial.printf("PID: Kp=%.2f Ki=%.2f Kd=%.2f\n", Kp, Ki, Kd);
            pid_reset();
        }
    }
    else if (cmd.startsWith("step "))
    {
        // High-frequency step response: "step <target%> <duration_ms>"
        // Logs at 1kHz for PID tuning
        int space = cmd.indexOf(' ', 5);
        float step_target = cmd.substring(5, space > 0 ? space : cmd.length()).toFloat() / 100.0f;
        int duration_ms = space > 0 ? cmd.substring(space + 1).toInt() : 3000;
        if (duration_ms < 100)
            duration_ms = 3000;
        if (duration_ms > 10000)
            duration_ms = 10000;

        Serial.println("# Step response test at 1kHz");
        Serial.printf("# Target: %.1f%%, Duration: %dms\n", step_target * 100, duration_ms);
        Serial.printf("# PID: Kp=%.2f Ki=%.2f Kd=%.2f\n", Kp, Ki, Kd);
        Serial.println("# time_ms,position,target,motor_cmd");

        motor_enable(true);
        pid_reset();
        target_position = step_target;

        unsigned long start = millis();
        while (millis() - start < (unsigned long)duration_ms)
        {
            // Read sensor
            raw_pot = read_adc_averaged(PIN_POT_SENSE);
            current_position = (float)(raw_pot - cal_min) / (cal_max - cal_min);
            current_position = constrain(current_position, 0.0f, 1.0f);

            // PID control
            float error = target_position - current_position;
            float dt = 0.001f; // 1ms
            float output = pid_compute(target_position, current_position, dt);
            int16_t motor_val = constrain((int)(output * 255), -255, 255);
            if (motor_val > 0 && motor_val < 60)
                motor_val = 60;
            if (motor_val < 0 && motor_val > -60)
                motor_val = -60;
            if (abs(error) < POSITION_DEADBAND)
                motor_val = 0;
            motor_set(motor_val);

            // Log
            Serial.printf("%lu,%.2f,%.2f,%d\n",
                          millis() - start,
                          current_position * 100,
                          target_position * 100,
                          motor_val);

            delayMicroseconds(1000); // 1kHz
        }

        motor_set(0);
        Serial.println("# Done");
    }
    else if (cmd == "status")
    {
        const char *state_names[] = {"IDLE", "DEMO", "POSITION", "CAL_MIN", "CAL_MAX", "MANUAL", "TOUCH"};
        Serial.println("=== Motor Fader Status ===");
        Serial.printf("State: %s\n", state_names[app_state]);
        Serial.printf("Position: raw=%d normalized=%.1f%% target=%.1f%%\n",
                      raw_pot, current_position * 100, target_position * 100);
        Serial.printf("Current: raw=%d (stall threshold=%d)\n",
                      raw_current, current_stall);
        Serial.printf("Touch: %s (raw=%d, threshold=%d)\n",
                      is_touched ? "TOUCHED" : "no",
                      touchRead(PIN_TOUCH_SENSE), TOUCH_THRESHOLD);
        Serial.printf("Calibration: %s (min=%d max=%d)\n",
                      calibrated ? "yes" : "no", cal_min, cal_max);
        Serial.printf("PID: Kp=%.2f Ki=%.2f Kd=%.2f\n", Kp, Ki, Kd);
    }
    else if (cmd == "touch")
    {
        // Monitor touch sensor for 10 seconds
        Serial.println("Touch sensor monitor (10 seconds)");
        Serial.println("Touch the fader to see the values change...");
        Serial.println("# time_ms,touch_raw,is_touched");
        unsigned long start = millis();
        while (millis() - start < 10000)
        {
            uint16_t touch_val = touchRead(PIN_TOUCH_SENSE);
            Serial.printf("%lu,%d,%s\n",
                          millis() - start,
                          touch_val,
                          touch_val < TOUCH_THRESHOLD ? "TOUCHED" : "no");
            delay(100); // 10Hz for readability
        }
        Serial.println("# Done");
    }
    else if (cmd == "scan")
    {
        // Scan all ADC pins to find the potentiometer
        Serial.println("Scanning ADC channels...");
        int pins[] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
        for (int i = 0; i < 10; i++)
        {
            int val = analogRead(pins[i]);
            Serial.printf("  GPIO%d: %d\n", pins[i], val);
        }
        Serial.println("Move fader and run 'scan' again to see which changes");
    }
    else if (cmd == "gpio")
    {
        // Test GPIO directly - detach PWM first
        Serial.println("Testing GPIO pins directly...");
        Serial.printf("Pins: IN1=GPIO%d, IN2=GPIO%d, SLEEP=GPIO%d\n",
                      PIN_MOTOR_IN1, PIN_MOTOR_IN2, PIN_MOTOR_SLEEP);

        // Detach PWM and set as regular GPIO
        ledcDetachPin(PIN_MOTOR_IN1);
        ledcDetachPin(PIN_MOTOR_IN2);
        pinMode(PIN_MOTOR_IN1, OUTPUT);
        pinMode(PIN_MOTOR_IN2, OUTPUT);

        Serial.println("Setting SLEEP=HIGH to enable driver");
        digitalWrite(PIN_MOTOR_SLEEP, HIGH);
        delay(100);

        Serial.println("IN1=HIGH, IN2=LOW for 3 sec... WATCH FADER!");
        digitalWrite(PIN_MOTOR_IN1, HIGH);
        digitalWrite(PIN_MOTOR_IN2, LOW);
        delay(3000);

        Serial.println("IN1=LOW, IN2=HIGH for 3 sec... WATCH FADER!");
        digitalWrite(PIN_MOTOR_IN1, LOW);
        digitalWrite(PIN_MOTOR_IN2, HIGH);
        delay(3000);

        Serial.println("Stopping - both LOW");
        digitalWrite(PIN_MOTOR_IN1, LOW);
        digitalWrite(PIN_MOTOR_IN2, LOW);

        // Re-attach PWM
        ledcAttachPin(PIN_MOTOR_IN1, PWM_CHANNEL_IN1);
        ledcAttachPin(PIN_MOTOR_IN2, PWM_CHANNEL_IN2);

        Serial.println("Done - did the motor move at all?");
    }
    else if (cmd == "steps")
    {
        // Step through positions with PID control and logging
        Serial.println("# Step demo with PID control");
        Serial.println("# time_ms,target_pct,actual_pct,error_pct,motor_cmd,current");
        motor_enable(true);

        int positions[] = {25, 50, 75, 100, 75, 50, 25, 0};
        int num_positions = 8;
        unsigned long start_time = millis();

        // PID state
        float integral = 0;
        float last_error = 0;

        // PID gains - tuned for smooth motion
        float kp = 8.0f; // Proportional
        float ki = 0.5f; // Integral
        float kd = 2.0f; // Derivative

        for (int i = 0; i < num_positions; i++)
        {
            float target = positions[i] / 100.0f;
            Serial.printf("# Moving to %d%%\n", positions[i]);

            // Reset integral for each new target
            integral = 0;
            last_error = target - current_position;

            // Move until we reach target (with timeout)
            unsigned long move_start = millis();
            int settled_count = 0;

            while (millis() - move_start < 5000)
            { // 5 sec timeout per position
                read_sensors();
                float error = target - current_position;

                // PID calculation
                integral += error * 0.02f;                   // dt = 20ms
                integral = constrain(integral, -0.5f, 0.5f); // Anti-windup
                float derivative = (error - last_error) / 0.02f;
                last_error = error;

                float output = kp * error + ki * integral + kd * derivative;

                // Scale to motor range and apply deadband
                int motor_cmd = 0;
                if (abs(error) < 0.02f)
                { // Within 2%
                    motor_cmd = 0;
                    settled_count++;
                }
                else
                {
                    motor_cmd = constrain((int)(output * 255), -255, 255);
                    // Minimum PWM to overcome friction
                    if (motor_cmd > 0 && motor_cmd < 80)
                        motor_cmd = 80;
                    if (motor_cmd < 0 && motor_cmd > -80)
                        motor_cmd = -80;
                    settled_count = 0;
                }

                motor_set(motor_cmd);

                // Log: time, target, actual, error, motor_cmd, current
                Serial.printf("%lu,%.1f,%.1f,%.1f,%d,%d\n",
                              millis() - start_time,
                              target * 100,
                              current_position * 100,
                              error * 100,
                              motor_cmd,
                              raw_current);

                // Consider settled if within deadband for 5 consecutive reads
                if (settled_count >= 5)
                    break;

                delay(20); // 50Hz control loop
            }

            // Stop and pause
            motor_set(0);
            Serial.printf("# Reached %.1f%%, pausing 500ms\n", current_position * 100);
            delay(500);
        }

        motor_set(0);
        motor_enable(false);
        Serial.println("# Step demo complete!");
    }
    else if (cmd == "log")
    {
        // High frequency logging for 5 seconds
        Serial.println("# Logging for 5 seconds (move fader by hand to see response)");
        Serial.println("# time_ms,raw_adc,position_pct,current");
        unsigned long start = millis();
        while (millis() - start < 5000)
        {
            read_sensors();
            Serial.printf("%lu,%d,%.2f,%d\n",
                          millis() - start,
                          raw_pot,
                          current_position * 100,
                          raw_current);
            delay(20); // 50Hz
        }
        Serial.println("# Logging complete");
    }
    else if (cmd == "help" || cmd == "?")
    {
        Serial.println("Commands:");
        Serial.println("  demo       - Start back-and-forth demo");
        Serial.println("  stop       - Stop motor");
        Serial.println("  cal        - Run endstop calibration");
        Serial.println("  pos <0-100> - Set position percentage");
        Serial.println("  motor <-255..255> - Manual motor control");
        Serial.println("  pid <Kp> <Ki> <Kd> - Set PID gains");
        Serial.println("  status     - Show system status");
        Serial.println("  touch      - Monitor touch sensor (10s)");
        Serial.println("  scan       - Scan ADC pins");
        Serial.println("  help       - Show this message");
        Serial.println("\nTouch override: Touch fader during pos/demo to take control");
    }
}

// ============================================================================
// Touch Override Handler
// ============================================================================

void handle_touch_override()
{
    // Check for touch during position control modes
    if (app_state == STATE_POSITION || app_state == STATE_DEMO)
    {
        if (is_touched)
        {
            // User touched fader - switch to override mode
            state_before_touch = app_state;
            app_state = STATE_TOUCH_OVERRIDE;
            motor_set(0); // Release motor immediately
            Serial.println("Touch detected - motor released");
        }
    }
    else if (app_state == STATE_TOUCH_OVERRIDE)
    {
        if (!is_touched)
        {
            // User released fader - update target to current position and resume
            target_position = current_position;
            pid_reset();
            app_state = state_before_touch;
            Serial.printf("Touch released - target updated to %.1f%%\n", target_position * 100);
        }
        else
        {
            // While touched, follow user movement (update target to match)
            target_position = current_position;
        }
    }
}

// ============================================================================
// Control Loop
// ============================================================================

void control_loop()
{
    read_sensors();

    // Handle touch override first (before normal control)
    handle_touch_override();

    switch (app_state)
    {
    case STATE_DEMO:
        demo_update();
        // Fall through to position control
        [[fallthrough]];

    case STATE_POSITION:
    {
        float error = target_position - current_position;

        // Check deadband - stop if close enough
        if (abs(error) < POSITION_DEADBAND)
        {
            motor_set(0);
            pid_reset();
        }
        else
        {
            // PID control
            float dt = 1.0f / CONTROL_LOOP_HZ;
            float output = pid_compute(target_position, current_position, dt);

            // Scale PID output to motor range (-255 to 255)
            int16_t motor_val = constrain((int)(output * 255), -255, 255);

            // Minimum PWM to overcome static friction
            if (motor_val > 0 && motor_val < 60)
                motor_val = 60;
            if (motor_val < 0 && motor_val > -60)
                motor_val = -60;

            motor_set(motor_val);
        }
    }
    break;

    case STATE_CALIBRATING_MIN:
    case STATE_CALIBRATING_MAX:
        calibration_process();
        break;

    case STATE_TOUCH_OVERRIDE:
        // Motor is off, just tracking user position
        // Handled in handle_touch_override()
        break;

    case STATE_MANUAL:
    case STATE_IDLE:
    default:
        break;
    }
}

// ============================================================================
// Setup & Loop
// ============================================================================

void setup()
{
    Serial.begin(115200);
    delay(1000); // Wait for USB CDC

    Serial.println("\n=================================");
    Serial.println("Motor Fader Firmware v1.0");
    Serial.println("ESP32-S3 + DRV8210P + ALPS Fader");
    Serial.println("=================================\n");

    // Configure ADC
    analogReadResolution(12);
    analogSetAttenuation(ADC_11db);

    // Initialize motor
    motor_init();

    // Configure touch
    touchSetCycles(0x1000, 0x1000);

    // Auto-start demo on boot
    delay(500);
    app_state = STATE_DEMO;
    demo_start();
    Serial.println("Type 'demo' to start motor demo\n");
}

void loop()
{
    // Process serial commands
    process_serial();

    // Run control loop at fixed rate
    unsigned long now = micros();
    if (now - last_control_time >= CONTROL_PERIOD_US)
    {
        last_control_time = now;
        control_loop();
    }

    // Periodic status (every 5 seconds, only during calibration/demo)
    static unsigned long last_status = 0;
    if ((app_state == STATE_CALIBRATING_MIN || app_state == STATE_CALIBRATING_MAX || app_state == STATE_DEMO) && millis() - last_status > 5000)
    {
        last_status = millis();
        Serial.printf("pos=%.1f%% target=%.1f%% current=%d touch=%d\n",
                      current_position * 100, target_position * 100,
                      raw_current, is_touched);
    }
}
