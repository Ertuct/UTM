#include <HX711_ADC.h>
#include <AccelStepper.h>

// --- PIN TANIMLAMALARI (Senin eski koduna göre güncellendi) ---
const int HX711_dout = 2; // Eski kodunda 4
const int HX711_sck = 3;  // Eski kodunda 5

// Motor Pinleri (Bunlar hala 9 ve 8, değiştirmek istersen buradan değiştir)
const int MOTOR_STEP_PIN = 9;
const int MOTOR_DIR_PIN = 8;

// --- AYARLAR ---
float calibrationValue = -14.0; // SENİN ESKİ KALİBRASYON DEĞERİN
const float LEAD_SCREW_PITCH = 2.0; // mm (Vidanın tur başına ilerlemesi)
const int STEPS_PER_REV = 200;      // Motorun adım sayısı
const int MICROSTEPS = 16;          // Sürücü üzerindeki ayar
float stepsPerMM = (STEPS_PER_REV * MICROSTEPS) / LEAD_SCREW_PITCH;

// --- NESNELER ---
HX711_ADC LoadCell(HX711_dout, HX711_sck);
AccelStepper stepper(AccelStepper::DRIVER, MOTOR_STEP_PIN, MOTOR_DIR_PIN);

// --- DEĞİŞKENLER ---
bool isRunning = false;
int motorDirection = 0; 
unsigned long lastSendTime = 0;
const int dataInterval = 50; // Veri gönderme sıklığı (ms)

void setup() {
  Serial.begin(57600); // Eski kodundaki hız bu, Python da buna uyacak.
  delay(10);
  
  // Loadcell Başlatma (Senin eski kodundaki mantıkla)
  LoadCell.begin();
  unsigned long stabilizingtime = 2000; 
  boolean _tare = true; 
  LoadCell.start(stabilizingtime, _tare);
  LoadCell.setCalFactor(calibrationValue); 

  // Motor Başlatma
  stepper.setMaxSpeed(2000); 
  stepper.setAcceleration(1000);
}

void loop() {
  // 1. LOADCELL GÜNCELLEME (Bu kütüphane için ZORUNLU)
  // Bu fonksiyon her döngüde çağrılmalı ki veri işlensin
  LoadCell.update();

  // 2. PYTHON'DAN KOMUT DİNLEME
  if (Serial.available() > 0) {
    char command = Serial.read();
    
    if (command == '1') { // Çekme
      motorDirection = 1;
      isRunning = true;
    } 
    else if (command == '2') { // Basma
      motorDirection = -1;
      isRunning = true;
    } 
    else if (command == '0') { // Durdur
      isRunning = false;
      stepper.stop(); 
    }
    else if (command == 'Z') { // Sıfırla
      LoadCell.tareNoDelay(); // Bu kütüphanenin sıfırlama komutu farklıdır
      stepper.setCurrentPosition(0);
      Serial.println("ZEROED"); 
    }
  }

  // 3. MOTOR HAREKETİ
  if (isRunning) {
    stepper.setSpeed(motorDirection * 600); 
    stepper.runSpeed();
  }

  // 4. VERİ GÖNDERME
  // LoadCell.getData() yeni veri hazır olmasa bile son okunanı verir, bu güvenlidir.
  unsigned long currentMillis = millis();
  if (currentMillis - lastSendTime >= dataInterval) {
    lastSendTime = currentMillis;
    
    float force = LoadCell.getData(); // Okunan ağırlık
    float currentSteps = stepper.currentPosition();
    float distance = currentSteps / stepsPerMM;

    // Format: "Kuvvet,Mesafe"
    Serial.print(force);
    Serial.print(",");
    Serial.println(distance);
  }
}