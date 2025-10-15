#include <Arduino.h>

static const uint8_t PIN_SENSOR = A0;
const float VREF = 5.0f;
const int ADC_MAX = 1023;

void setup() {
  pinMode(PIN_SENSOR, INPUT);
  Serial.begin(9600);
  while (!Serial) {}
  Serial.println(F("timestamp_ms,raw,volts"));
}

void loop() {
  int raw = analogRead(PIN_SENSOR);
  float volts = (raw * 1.0f / ADC_MAX) * VREF;

  Serial.print(millis());
  Serial.print(',');
  Serial.print(raw);
  Serial.print(',');
  Serial.println(volts, 4);

  delay(20); // ~50 Hz
}