#include <Arduino.h>

// --- Configuration Settings ---
const int ANALOG_PIN = A0;              // Analog pin to read from
const int TRIGGER_THRESHOLD = 527;       // Minimum analog value (0-1023) to consider the start of a peak event
const unsigned long PEAK_WINDOW_MS = 50; // How long to actively search for the max value after the trigger
const unsigned long COOLDOWN_TIME_MS = 3000; // Time to ignore signals after a primary peak is recorded (5 seconds)
const int MAX_SAMPLES = 100;            // Maximum number of primary peak readings to store

// --- Data Storage ---
// Array (vector) to store the primary peak readings (0-1023)
int primaryPeakReadings[MAX_SAMPLES];
int sampleIndex = 0;                    // Counter for stored readings

// --- State Variables ---
enum State { WAITING_FOR_PEAK, RECORDING_PEAK, COOLDOWN };
State currentState = WAITING_FOR_PEAK;

int currentPeak = 0;                    // Stores the maximum value recorded during the event
unsigned long stateChangeTime;          // Stores the time when the current state began

void setup() {
  // Use a fast baud rate for efficient data transfer
  Serial.begin(115200); 
  Serial.println("--- Starting Primary Peak Voltage Capture ---");
  Serial.print("Target Samples: ");
  Serial.println(MAX_SAMPLES);
}

void loop() {
  // Stop if all required samples are collected
  if (sampleIndex >= MAX_SAMPLES) {
    Serial.println("\n--- ALL SAMPLES COLLECTED ---");
    // Print the raw data, one peak reading per line, for easy logging to a TXT file
    Serial.println("START_DATA_CAPTURE");
    for (int i = 0; i < MAX_SAMPLES; i++) {
      Serial.println(primaryPeakReadings[i]);
    }
    Serial.println("END_DATA_CAPTURE");
    while (true); // Halt the program
  }

  int sensorValue = analogRead(ANALOG_PIN);

  switch (currentState) {
    
    case WAITING_FOR_PEAK:
      if (sensorValue >= TRIGGER_THRESHOLD) {
        // Serial.println("Triggered! Starting peak recording..."); // Optional debug print
        currentPeak = sensorValue;    
        stateChangeTime = millis();   
        currentState = RECORDING_PEAK;
      }
      break;

    case RECORDING_PEAK:
      if (millis() - stateChangeTime < PEAK_WINDOW_MS) {
        if (sensorValue > currentPeak) {
          currentPeak = sensorValue; 
        }
      } else {
        // Peak window ended. Store the result and start cooldown.
        primaryPeakReadings[sampleIndex] = currentPeak;
        
        
       
        Serial.println(currentPeak); // Print the result during the process
        
        sampleIndex++;                  
        stateChangeTime = millis();     
        currentState = COOLDOWN;
      }
      break;

    case COOLDOWN:
      if (millis() - stateChangeTime >= COOLDOWN_TIME_MS) {
        // Serial.println("Cooldown finished. Ready for next event."); // Optional debug print
        currentState = WAITING_FOR_PEAK; 
        currentPeak = 0;                 
      }
      break;
  }
}