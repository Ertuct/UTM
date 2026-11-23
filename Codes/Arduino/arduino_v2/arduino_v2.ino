#include "HX711.h"

// --- PINS ---
const int stepPin = 8;
const int dirPin = 9;
const int doutPin = 3;
const int clkPin = 2;
const int ledPin = 13; // Visual Debugger

// --- SETTINGS ---
// INCREASED DELAY: 200 microseconds is much slower/safer.
// If it works now, you can lower this number later to go faster.
int pulseDelay = 200; 

HX711 scale;

void setup() {
  Serial.begin(9600);
  pinMode(stepPin, OUTPUT);
  pinMode(dirPin, OUTPUT);
  pinMode(ledPin, OUTPUT);
  
  scale.begin(doutPin, clkPin);
  scale.set_scale();
  scale.tare(); 
  
  // Blink twice to say "I am Reset"
  digitalWrite(ledPin, HIGH); delay(200); digitalWrite(ledPin, LOW); delay(200);
  digitalWrite(ledPin, HIGH); delay(200); digitalWrite(ledPin, LOW);
  
  Serial.println("READY");
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command.startsWith("MOVE:")) {
      digitalWrite(ledPin, HIGH); // Turn ON LED while moving
      
      int firstColon = command.indexOf(':');
      int secondColon = command.lastIndexOf(':');
      long steps = command.substring(firstColon + 1, secondColon).toInt();
      int direction = command.substring(secondColon + 1).toInt();

      moveMotor(steps, direction);
      
      digitalWrite(ledPin, LOW); // Turn OFF LED when done
      Serial.println("DONE");
    }
    else if (command == "READ_LOAD") {
      Serial.println(scale.get_units(10), 4);
    }
    else if (command == "TARE") {
      scale.tare();
      Serial.println("TARED");
    }
  }
}

void moveMotor(long steps, int dir) {
  digitalWrite(dirPin, dir); 
  for (long i = 0; i < steps; i++) {
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(pulseDelay);
    digitalWrite(stepPin, LOW);
    delayMicroseconds(pulseDelay);
  }
}