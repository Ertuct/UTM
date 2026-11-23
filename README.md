# Modular Universal Testing Machine (UTM) for Small-Scale Material Characterization

An open-source, affordable, and modular benchtop Universal Testing Machine (UTM) developed from scratch for tensile and compression characterization of polymers, composites, and thin sheet materials.

Presented as an oral research paper at the **16th International Congress on Engineering and Technology Management (ICETM 2026)**, Istanbul, Türkiye.

---

## 👥 Authors & Academic Affiliation

- **Celal Topcu** ([celaltopcu.com](https://celaltopcu.com)) — Lead Engineer & Developer
- **Egehan Sönmez** — Project Partner & Mechanical Design
- **Assoc. Prof. Dr. Sinan Güçlüer** — Faculty Member, Dept. of Mechanical Engineering, Aydın Adnan Menderes University
- **Assoc. Prof. Dr. Adem Özçelik** — Thesis Advisor, Dept. of Mechanical Engineering, Aydın Adnan Menderes University

---

## 📄 Academic Citation & Proceedings

> Celal Topcu, Egehan Sönmez, Sinan Güçlüer, Adem Özçelik.  
> **"Design and Implementation of a Low-Cost, Modular Universal Testing Machine for Small-Scale Material Characterization."**  
> *16th International Congress on Engineering and Technology Management (ICETM 2026)*, Istanbul, Türkiye, August 15, 2026.  
> Proceedings pp. 51–58, **E-ISBN: 978-625-92029-4-5** (Güven Plus Grup Danışmanlık A.Ş. Yayınları).

Full proceedings book is included in this repository: [`16. Uluslararası Mühendislik ve Teknoloji Yönetimi Kongresi Bildiri Kitabı.pdf`](./16.%20Uluslararası%20Mühendislik%20ve%20Teknoloji%20Yönetimi%20Kongresi%20Bildiri%20Kitabı.pdf).

---

## 🛠️ System Architecture

### 1. Mechanical System (`/Drawings`)
- **Frame:** Dual-column structural aluminum extrusion (2020/2040 profiles) ensuring high structural rigidity under axial tension.
- **Powertrain:** NEMA 17 high-torque stepper motor coupled to precision T8 leadscrews with linear ball-bearing guide rails.
- **Fixtures:** Modular grips (stationary and moving crosshead) designed for ASTM D638 standard dog-bone specimens.
- **CAD Formats:** Complete 3D models available in STEP (`.step`), Fusion 360 (`.f3d`), SolidWorks (`.sldprt`), and 3D-printable STL (`.stl`).

### 2. Electronics & Instrumentation (`/Codes/Arduino`)
- **Microcontroller:** Arduino Mega 2560.
- **Force Measurement:** S-type precision load cell paired with a 24-bit HX711 analog-to-digital converter (ADC) amplifier.
- **Motion Control:** A4988 / TMC stepper driver with microstepping and dual endstop limit switches for safe travel boundaries.

### 3. Software & Real-Time DAQ (`/Codes/App UI and Codes` & `UTM-APP.py`)
- **Desktop GUI:** Custom Python application built with PyQt / CustomTkinter.
- **Features:**
  - Real-time serial data acquisition (DAQ) and tare calibration.
  - Live stress-strain ($\sigma$-$\varepsilon$) curve plotting during test runs.
  - Automated mechanical property calculation: Elastic Modulus ($E$), Yield Strength ($\sigma_y$), and Ultimate Tensile Strength (UTS).
  - Raw test data export to `.csv` and `.xlsx` for academic plotting.

---

## 📂 Repository Contents

```
├── 16. Uluslararası Mühendislik ve Teknoloji Yönetimi Kongresi Bildiri Kitabı.pdf  # Full Congress Proceedings Book
├── Design and Implementation of a Low-Cost, Modular.pptx                           # Presentation Slides
├── Full-proceeding_.docx                                                           # Research Paper Manuscript
├── UTM_Presentation_Certificate.jpeg                                               # ICETM 2026 Presentation Certificate
├── UTM-APP.py                                                                      # Python GUI & DAQ Application
├── UTM-Graph-Creator.py                                                            # Post-processing Graph Generation Script
├── Codes/
│   ├── Arduino/                                                                    # Firmware (.ino) for Arduino Mega
│   └── App UI and Codes/                                                           # GUI Source Code Versions
├── Drawings/
│   ├── Stl/                                                                        # 3D Printable STL Files & STEP Assembly
│   ├── Fusion 360 Çizimleri/                                                       # Native Fusion 360 Models (.f3d)
│   └── *.sldprt, *.dxf                                                             # SolidWorks and DXF Profiles
├── Photos/                                                                         # Machine Setup & Experimental Test Rigs
└── Test Results/                                                                   # Experimental Test Runs (Filamix, Filameon, ELAS PLA)
```

---

## 📊 Experimental Results

Experimental validation was conducted using ASTM D638 Type IV tensile specimens across multiple filament types:
- **ELAS 3D PLA Pro**
- **Filameon PLA**
- **Filamix PLA+ (Blue & Black)**

All stress-strain curves, tensile logs, and raw data are located under the [`/Test Results`](./Test%20Results) directory.

---

## 📬 Contact & Portfolio

For questions, collaborations, or reproduction details:
- **Celal Topcu:** [contact@celaltopcu.com](mailto:contact@celaltopcu.com) | [celaltopcu.com](https://celaltopcu.com)
