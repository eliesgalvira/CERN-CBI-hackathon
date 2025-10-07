#include <Arduino.h>
#include <Servo.h>

static const int SERVO_PIN = 3;
Servo servo;

void setup() {
  servo.attach(SERVO_PIN);
  //servo.write(100); // glass marble
  //servo.write(129); // metal marble
  //servo.write(80); // plastic marble
}
    
void loop() {
    delay(5000); // wait a second
  // Sweep 0 -> 90
  for (int pos = 81; pos <= 100; pos++) {
    servo.write(pos);
    delay(10); // speed of sweep
  }
    delay(10000); // wait a second
    servo.write(129);
  // Sweep 90 -> 0
  for (int pos = 100; pos >= 80; pos--) {
    servo.write(pos);
    delay(10);
  }
}