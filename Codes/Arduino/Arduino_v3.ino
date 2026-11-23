#include "HX711.h"

// --- PIN TANIMLAMALARI ---
// Load Cell (HX711)
const int LOADCELL_DOUT_PIN = 2;
const int LOADCELL_SCK_PIN = 3;

// Step Motor Sürücü (TB6600 / CWD556 vb.)
const int STEP_PIN = 9;
const int DIR_PIN = 8;
const int ENA_PIN = 7; // Opsiyonel, genelde 5V'a bağlanır

// --- DEĞİŞKENLER ---
HX711 scale;
long current_steps = 0;
bool is_running = false;
float motor_speed_delay = 1000; // Başlangıç hızı (mikrosaniye)
int motor_direction = -1;       // 1: Çekme, -1: Basma

// Kalibrasyon Değerleri (Kendi sistemine göre güncelle)
// HX711 kütüphanesindeki set_scale fonksiyonu için
float calibration_factor = 2280.0; 

// 1mm gitmek için gereken adım sayısı (Sürücü ayarına göre değişir)
// Örn: 1000 adım motor * 50 redüktör / 2mm vida hatvesi = 25000 adım/mm
float steps_per_mm = 20000.0;

unsigned long last_send_time = 0;

void setup() {
  Serial.begin(9600);
  
  // Motor Pinleri
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  pinMode(ENA_PIN, OUTPUT);
  digitalWrite(ENA_PIN, LOW); // Motoru aktif et (Low/High sürücüye göre değişebilir)

  // Load Cell Başlatma
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.set_scale(calibration_factor);
  scale.tare(); // Açılışta dara al
}

void loop() {
  // 1. PYTHON'DAN KOMUT OKUMA
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); // Boşlukları temizle
    parseCommand(command);
  }

  // 2. MOTOR HAREKETİ (Test Başladıysa)
  if (is_running) {
    digitalWrite(DIR_PIN, motor_direction > 0 ? HIGH : LOW);
    
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(motor_speed_delay);
    digitalWrite(STEP_PIN, LOW);
    delayMicroseconds(motor_speed_delay);
    
    // Konum güncelle (Yönüne göre artır veya azalt)
    current_steps += motor_direction;
  }

  // 3. VERİ GÖNDERME (Her 100ms'de bir gönderir, Python'u boğmaz)
  if (millis() - last_send_time > 100) {
    sendDataToPython();
    last_send_time = millis();
  }
}

// --- YARDIMCI FONKSİYONLAR ---

void parseCommand(String cmd) {
  // START:10 -> 10mm/dk hızla başlat
  if (cmd.startsWith("START:")) {
    float speed_mm_min = cmd.substring(6).toFloat();
    
    // Yön Belirleme (Negatif hız basma testidir)
    if (speed_mm_min < 0) {
      motor_direction = -1;
      speed_mm_min = abs(speed_mm_min);
    } else {
      motor_direction = 1;
    }

    // Hız Hesabı (mm/dk -> delay mikrosaniye)
    // Delay = (60 * 1000000) / (steps_per_mm * mm_min * 2)
    // *2 çünkü her adımda HIGH ve LOW beklemesi var
    if (speed_mm_min > 0) {
      motor_speed_delay = (30000000.0) / (steps_per_mm * speed_mm_min);
    }
    
    is_running = true; // DÜZELTİLDİ: Testin başlaması için true olmalı
  }
  
  // STOP -> Durdur
  else if (cmd.equals("STOP")) {
    is_running = false;
  }
  
  // MOVE:5 -> 5mm manuel hareket et
  else if (cmd.startsWith("MOVE:")) {
    float dist = cmd.substring(5).toFloat();
    long steps_to_move = dist * steps_per_mm;
    int dir = (steps_to_move > 0) ? HIGH : LOW;
    steps_to_move = abs(steps_to_move);
    
    digitalWrite(DIR_PIN, dir);
    for (long i = 0; i < steps_to_move; i++) {
      digitalWrite(STEP_PIN, HIGH);
      delayMicroseconds(40); // DÜZELTİLDİ: Makinenin kilitlenmemesi için hızlandırıldı
      digitalWrite(STEP_PIN, LOW);
      delayMicroseconds(40);
      
      // Konumu güncelle
      if (dir == HIGH) current_steps++; else current_steps--;
    }
  }
  
  // TARE -> Dara Al (Sıfırla)
  else if (cmd.equals("TARE")) {
    scale.tare();
    current_steps = 0;
  }
}

void sendDataToPython() {
  // Kuvveti Oku (Load Cell)
  float force_n = scale.get_units(1); // 1 okumanın ortalaması (hızlı olması için)
  
  // Mesafeyi Hesapla (Adım -> mm)
  float dist_mm = current_steps / steps_per_mm;
  
  // Veriyi Formatla: "Kuvvet,Mesafe"
  Serial.print(force_n, 2); // Virgülden sonra 2 hane
  Serial.print(",");
  Serial.println(dist_mm, 2);
}