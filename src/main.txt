#include <Arduino.h>
#include <Servo.h>

// --- Pin Assignments ---
const int ANALOG_PIN = A0;     // Sensor input
const int SERVO_SORT_PIN = 5;  // Sorter servo

// --- Detection / Peak Capture Settings ---
const int TRIGGER_THRESHOLD = 527;            // Start of event
const unsigned long PEAK_WINDOW_MS = 50;      // Window to find max after trigger
const unsigned long COOLDOWN_TIME_MS = 3000;  // Ignore new events after sorting

// --- State Machine ---
enum State { WAITING_FOR_PEAK, RECORDING_PEAK, COOLDOWN };
State currentState = WAITING_FOR_PEAK;

int currentPeak = 0;
unsigned long stateChangeTime = 0;

// --- Sorter Servo ---
Servo sortServo;
int sortCurrentAngle = 100;  // Neutral-ish

// --- Classification ---
enum Material { MAT_UNKNOWN, MAT_PLASTIC, MAT_GLASS, MAT_METAL };

// 527–539 plastic, 540–554 glass, 555–650 metal
Material classifyPeak(int val) {
  if (val >= 555 && val <= 650) return MAT_METAL;
  if (val >= 540 && val <= 554) return MAT_GLASS;
  if (val >= 527 && val <= 539) return MAT_PLASTIC;
  return MAT_UNKNOWN;
}

void moveSorterFor(Material m) {
  int target = sortCurrentAngle;
  switch (m) {
    case MAT_PLASTIC:
      target = 80;
      break;
    case MAT_GLASS:
      target = 100;
      break;
    case MAT_METAL:
      target = 125;
      break;
    default:
      target = sortCurrentAngle;  // No move for unknown
      break;
  }
  if (target != sortCurrentAngle) {
    sortServo.write(target);
    sortCurrentAngle = target;
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("--- Detector + Sorter (with enforced cooldown) ---");

  sortServo.attach(SERVO_SORT_PIN);
  sortServo.write(sortCurrentAngle);  // Initialize

  currentState = WAITING_FOR_PEAK;
  currentPeak = 0;
  stateChangeTime = millis();
}

void loop() {
  int sensorValue = analogRead(ANALOG_PIN);

  switch (currentState) {
    case WAITING_FOR_PEAK: {
      // Wait for trigger crossing
      if (sensorValue >= TRIGGER_THRESHOLD) {
        currentPeak = sensorValue;
        stateChangeTime = millis();
        currentState = RECORDING_PEAK;
        // Serial.println("Triggered: recording peak...");
      }
      break;
    }

    case RECORDING_PEAK: {
      // Track the maximum within the peak window
      if (millis() - stateChangeTime < PEAK_WINDOW_MS) {
        if (sensorValue > currentPeak) currentPeak = sensorValue;
      } else {
        // Window done: classify, move sorter, then immediately enter cooldown
        Material m = classifyPeak(currentPeak);
        moveSorterFor(m);

        // Debug
        Serial.print("Peak: ");
        Serial.print(currentPeak);
        Serial.print(" -> ");
        switch (m) {
          case MAT_PLASTIC:
            Serial.println("PLASTIC (->80°)");
            break;
          case MAT_GLASS:
            Serial.println("GLASS (->100°)");
            break;
          case MAT_METAL:
            Serial.println("METAL (->129°)");
            break;
          default:
            Serial.println("UNKNOWN (no move)");
            break;
        }

        // Start cooldown immediately to ignore any disturbances
        stateChangeTime = millis();
        currentPeak = 0;
        currentState = COOLDOWN;
      }
      break;
    }

    case COOLDOWN: {
      // Ignore all readings during cooldown so servo motion can't retrigger
      if (millis() - stateChangeTime >= COOLDOWN_TIME_MS) {
        currentState = WAITING_FOR_PEAK;
      }
      break;
    }
  }
}