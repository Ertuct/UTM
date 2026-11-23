#include "HX711.h"

const int LOADCELL_DOUT_PIN = 2;
const int LOADCELL_SCK_PIN = 3;

const int STEP_PIN = 9;
const int DIR_PIN = 8;
const int ENA_PIN = 7;

HX711 scale;
long current_steps = 0;
bool is_running = false;
float motor_speed_delay = 1000;
int motor_direction = -1;

float calibration_factor = 2280.0; 
float steps_per_mm = 20000.0;

unsigned long last_send_time = 0;

void setup() {
  Serial.begin(9600);
  
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  pinMode(ENA_PIN, OUTPUT);
  digitalWrite(ENA_PIN, LOW);

  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.set_scale(calibration_factor);
  scale.tare();
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    parseCommand(command);
  }

  if (is_running) {
    digitalWrite(DIR_PIN, motor_direction > 0 ? HIGH : LOW);
    
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(motor_speed_delay);
    digitalWrite(STEP_PIN, LOW);
    delayMicroseconds(motor_speed_delay);
    
    current_steps += motor_direction;
  }

  if (millis() - last_send_time > 100) {
    sendDataToPython();
    last_send_time = millis();
  }
}

void parseCommand(String cmd) {
  if (cmd.startsWith("START:")) {
    float speed_mm_min = cmd.substring(6).toFloat();
    
    if (speed_mm_min < 0) {
      motor_direction = -1;
      speed_mm_min = abs(speed_mm_min);
    } else {
      motor_direction = 1;
    }

    if (speed_mm_min > 0) {
      motor_speed_delay = (30000000.0) / (steps_per_mm * speed_mm_min);
    }
    
    is_running = true;
  }
  else if (cmd.equals("STOP")) {
    is_running = false;
  }
  else if (cmd.startsWith("MOVE:")) {
    float dist = cmd.substring(5).toFloat();
    long steps_to_move = dist * steps_per_mm;
    int dir = (steps_to_move > 0) ? HIGH : LOW;
    steps_to_move = abs(steps_to_move);
    
    digitalWrite(DIR_PIN, dir);
    
    int d = 500;
    for (long i = 0; i < steps_to_move; i++) {
      digitalWrite(STEP_PIN, HIGH);
      delayMicroseconds(d);
      digitalWrite(STEP_PIN, LOW);
      delayMicroseconds(d);
      
      if (i < 2000 && d > 40) d -= 1;
      else if (i > steps_to_move - 2000 && d < 500) d += 1;
      
      if (dir == HIGH) current_steps++; else current_steps--;
    }
  }
  else if (cmd.equals("TARE")) {
    scale.tare();
    current_steps = 0;
  }
}

void sendDataToPython() {
  float force_n = scale.get_units(1);
  float dist_mm = current_steps / steps_per_mm;
  
  Serial.print(force_n, 2);
  Serial.print(",");
  Serial.println(dist_mm, 2);
}