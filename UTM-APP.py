import sys
import threading
import time
import os
from collections import deque
from datetime import datetime

# 1. Library Check
try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import customtkinter as ctk
    from fpdf import FPDF
    import serial
    import serial.tools.list_ports
    import pandas as pd
    from tkinter import filedialog, messagebox
except ImportError as e:
    print(f"Library Error: {e}")
    print("Please run: pip install customtkinter matplotlib pyserial fpdf pandas openpyxl")
    sys.exit()

# 2. Appearance Settings
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# --- STANDARDS DICTIONARY ---
STANDARDS = {
    "Custom (Manual Input)": {"area": "", "lo": ""},
    "ASTM D638 Type I": {"area": "52.0", "lo": "50.0"},  
    "ASTM D638 Type IV": {"area": "24.0", "lo": "25.0"}, 
    "ASTM D638 Type V": {"area": "12.72", "lo": "7.62"}, 
    "ISO 527-2 Type 1A": {"area": "40.0", "lo": "50.0"}  
}

class UTMApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.geometry("1200x850")
        self.title("UTM CONTROL")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.ser = None
        self.running = False
        self.current_raw_force = 0.0
        self.current_raw_dist = 0.0
        
        # Graph & Excel Data
        self.data_t = []
        self.data_y = []
        self.data_x = []
        
        self.excel_data = {
            "Time (s)": [],
            "Force (N)": [],
            "Distance (mm)": [],
            "Stress (MPa)": [],
            "Strain (%)": []
        }
        
        self.force_buffer = deque(maxlen=5)
        
        self.factor_force = 1.0
        self.factor_dist = 1.0
        self.invert_motor = False
        
        self.setup_ui()
        self.scan_ports()
        
        self.stop_thread = False
        threading.Thread(target=self.serial_reader, daemon=True).start()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- LEFT PANEL ---
        self.sb = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sb.grid(row=0, column=0, sticky="nsew")
        self.sb.grid_propagate(False)

        ctk.CTkLabel(self.sb, text="UTM CONTROL", font=("Arial", 24, "bold")).pack(pady=20)

        self.fr_conn = ctk.CTkFrame(self.sb)
        self.fr_conn.pack(fill="x", padx=10, pady=5)
        self.cmb_port = ctk.CTkOptionMenu(self.fr_conn, values=["Select Port"])
        self.cmb_port.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(self.fr_conn, text="⟳", width=40, command=self.scan_ports).pack(side="left", padx=5)
        
        self.btn_conn = ctk.CTkButton(self.sb, text="CONNECT", fg_color="green", command=self.toggle_conn)
        self.btn_conn.pack(fill="x", padx=10, pady=5)

        self.btn_move_10 = ctk.CTkButton(self.sb, text="TEST: MOVE 10mm", fg_color="#8e44ad", command=self.test_move_10mm)
        self.btn_move_10.pack(fill="x", padx=10, pady=(15, 0))

        # --- TEST PARAMETERS ---
        ctk.CTkLabel(self.sb, text="Test Parameters", font=("Arial", 14, "bold")).pack(pady=(15, 5))
        
        self.cmb_standard = ctk.CTkOptionMenu(self.sb, values=list(STANDARDS.keys()), command=self.on_standard_change)
        self.cmb_standard.pack(fill="x", padx=10, pady=5)
        self.cmb_standard.set("Custom (Manual Input)")

        self.ent_area = ctk.CTkEntry(self.sb, placeholder_text="Area (mm²)")
        self.ent_area.pack(fill="x", padx=10, pady=5)
        
        self.ent_lo = ctk.CTkEntry(self.sb, placeholder_text="Gauge Length (Lo) (mm)")
        self.ent_lo.pack(fill="x", padx=10, pady=5)

        self.fr_speed = ctk.CTkFrame(self.sb, fg_color="transparent")
        self.fr_speed.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(self.fr_speed, text="Speed (mm/min):").pack(side="left", padx=5)
        self.ent_speed = ctk.CTkEntry(self.fr_speed, width=80)
        self.ent_speed.insert(0, "10") 
        self.ent_speed.pack(side="right", padx=5)

        # Main Control Buttons
        self.btn_start = ctk.CTkButton(self.sb, text="START TEST", height=50, fg_color="#27ae60", font=("Arial", 14, "bold"), command=self.start_test)
        self.btn_start.pack(fill="x", padx=10, pady=15)
        
        self.btn_stop = ctk.CTkButton(self.sb, text="STOP", fg_color="#c0392b", state="disabled", command=self.stop_test)
        self.btn_stop.pack(fill="x", padx=10, pady=5)
        
        # SIFIRLAMA BUTONLARI
        self.btn_reset = ctk.CTkButton(self.sb, text="RESET FOR NEW TEST", fg_color="gray", command=self.reset_data)
        self.btn_reset.pack(fill="x", padx=10, pady=5)

        self.btn_tare = ctk.CTkButton(self.sb, text="ZERO SENSORS (TARE)", fg_color="#d35400", command=self.send_tare)
        self.btn_tare.pack(fill="x", padx=10, pady=5)

        self.chk_inv = ctk.CTkCheckBox(self.sb, text="Invert Motor Direction", command=self.toggle_inv)
        self.chk_inv.pack(pady=10)

        # Export Buttons
        ctk.CTkLabel(self.sb, text="Export Data", font=("Arial", 12, "bold"), text_color="gray").pack(pady=(10,0))
        self.btn_excel = ctk.CTkButton(self.sb, text="EXPORT EXCEL", fg_color="#2980b9", command=self.save_excel)
        self.btn_excel.pack(fill="x", padx=10, pady=5)
        
        self.btn_pdf = ctk.CTkButton(self.sb, text="EXPORT PDF", fg_color="#d35400", command=self.save_pdf)
        self.btn_pdf.pack(fill="x", padx=10, pady=5)

        # --- RIGHT PANEL ---
        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.fr_cards = ctk.CTkFrame(self.main, fg_color="transparent")
        self.fr_cards.pack(fill="x", pady=10)
        
        self.card_y = self.create_card(self.fr_cards, "STRESS (MPa)", "#3498db")
        self.card_x = self.create_card(self.fr_cards, "STRAIN (%)", "#e91e63")
        self.card_t = self.create_card(self.fr_cards, "TIME (s)", "white")

        self.fig, self.ax = plt.subplots(figsize=(6,6), dpi=100)
        self.apply_dark_theme()
        
        self.line, = self.ax.plot([], [], color='cyan', linewidth=2)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.main)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def apply_dark_theme(self):
        self.fig.patch.set_facecolor('#2b2b2b')
        self.ax.set_facecolor('#2b2b2b')
        self.ax.tick_params(colors='white')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white') 
        self.ax.spines['right'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.ax.grid(True, linestyle='--', alpha=0.3, color='gray')
        self.ax.set_xlabel("Strain (%)")
        self.ax.set_ylabel("Stress (MPa)")

    def apply_light_theme(self):
        self.fig.patch.set_facecolor('white')
        self.ax.set_facecolor('white')
        self.ax.tick_params(colors='black')
        self.ax.spines['bottom'].set_color('black')
        self.ax.spines['top'].set_color('black') 
        self.ax.spines['right'].set_color('black')
        self.ax.spines['left'].set_color('black')
        self.ax.xaxis.label.set_color('black')
        self.ax.yaxis.label.set_color('black')
        self.ax.grid(True, linestyle='--', alpha=0.5, color='gray')
        self.ax.set_xlabel("Strain (%)")
        self.ax.set_ylabel("Stress (MPa)")

    def create_card(self, parent, title, color):
        f = ctk.CTkFrame(parent)
        f.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkLabel(f, text=title, text_color="gray", font=("Arial", 12, "bold")).pack(pady=5)
        l = ctk.CTkLabel(f, text="0.00", text_color=color, font=("Arial", 26, "bold"))
        l.pack(pady=5)
        return l

    # --- UI EVENTS ---
    def on_standard_change(self, selected_std):
        data = STANDARDS.get(selected_std)
        if data:
            self.ent_area.delete(0, 'end')
            self.ent_lo.delete(0, 'end')
            if selected_std != "Custom (Manual Input)":
                self.ent_area.insert(0, data["area"])
                self.ent_lo.insert(0, data["lo"])

    def scan_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.cmb_port.configure(values=ports if ports else ["Not Found"])
        if ports: self.cmb_port.set(ports[0])

    def toggle_conn(self):
        if not self.ser:
            selected_port = self.cmb_port.get()
            if selected_port in ["Select Port", "Not Found", "-"]:
                messagebox.showerror("Error", "Please click the refresh button (⟳) and select a valid port!")
                return
            try:
                self.ser = serial.Serial(selected_port, 9600, timeout=1)
                time.sleep(2)
                self.ser.write(b"TARE\n")
                self.btn_conn.configure(text="DISCONNECT", fg_color="red")
            except: messagebox.showerror("Error", "Could not connect to the selected port!")
        else:
            self.ser.close()
            self.ser = None
            self.btn_conn.configure(text="CONNECT", fg_color="green")

    def toggle_inv(self):
        self.invert_motor = bool(self.chk_inv.get())

    def send_tare(self):
        """Manuel sensör sıfırlama komutu"""
        if self.ser and self.ser.is_open:
            self.ser.write(b"TARE\n")
            messagebox.showinfo("Success", "Sensors Zeroed (Tared).")

    # --- CORE LOGIC ---
    def test_move_10mm(self):
        if not self.ser or not self.ser.is_open:
            messagebox.showerror("Error", "Please connect to the device first!")
            return
        dist = -10.0 if self.invert_motor else 10.0
        try:
            self.ser.write(f"MOVE:{dist}\n".encode())
            self.btn_stop.configure(state="normal")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send command: {e}")

    def serial_reader(self):
        while not self.stop_thread:
            if self.ser and self.ser.is_open:
                try:
                    if self.ser.in_waiting:
                        line = self.ser.readline().decode(errors='ignore').strip()
                        parts = line.split(',')
                        if len(parts) == 2: 
                            try:
                                r_f = float(parts[0])
                                r_d = float(parts[1])
                                
                                self.force_buffer.append(r_f)
                                avg_f = sum(self.force_buffer) / len(self.force_buffer)
                                if abs(avg_f) < 0.05: avg_f = 0.0
                                
                                self.current_raw_force = avg_f
                                self.current_raw_dist = r_d
                            except ValueError: pass
                except Exception: pass
            time.sleep(0.01)

    def start_test(self):
        if not self.ser:
            messagebox.showerror("Error", "Please connect to the device first!")
            return
        
        try:
            area = float(self.ent_area.get().replace(',', '.')) 
            lo = float(self.ent_lo.get().replace(',', '.'))
            speed = float(self.ent_speed.get().replace(',', '.'))
            if area <= 0 or lo <= 0 or speed <= 0: raise ValueError 
        except:
            messagebox.showerror("Validation Error", "Please enter valid, positive numeric values for Area, Length, and Speed.")
            return

        self.running = False
        
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.btn_move_10.configure(state="disabled")
        self.btn_tare.configure(state="disabled")
        
        try:
            if self.invert_motor: speed = -speed
            self.ser.write(f"START:{speed}\n".encode())
        except: pass
        
        self.running = True
        threading.Thread(target=self.test_loop, args=(area, lo), daemon=True).start()

    def test_loop(self, area, lo):
        self.data_t.clear()
        self.data_y.clear()
        self.data_x.clear()
        self.excel_data = {"Time (s)": [], "Force (N)": [], "Distance (mm)": [], "Stress (MPa)": [], "Strain (%)": []}
        
        start_time = time.time()
        
        while self.running:
            try:
                t = time.time() - start_time
                
                f = abs(self.current_raw_force * self.factor_force)
                d = abs(self.current_raw_dist * self.factor_dist)
                
                stress = f / area
                strain = (d / lo) * 100
                
                self.excel_data["Time (s)"].append(t)
                self.excel_data["Force (N)"].append(f)
                self.excel_data["Distance (mm)"].append(d)
                self.excel_data["Stress (MPa)"].append(stress)
                self.excel_data["Strain (%)"].append(strain)
                
                self.data_t.append(t)
                self.data_y.append(stress)
                self.data_x.append(strain)
                
                self.after(0, self.update_gui, stress, strain, t)
                time.sleep(0.1) 
            except: break

    def update_gui(self, y, x, t):
        self.card_y.configure(text=f"{y:.2f}")
        self.card_x.configure(text=f"{x:.2f}")
        self.card_t.configure(text=f"{t:.1f}")
        
        self.line.set_data(self.data_x, self.data_y)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

    def stop_test(self):
        self.running = False
        if self.ser: 
            try: self.ser.write(b"STOP\n")
            except: pass
            
        self.btn_start.configure(state="normal")
        self.btn_move_10.configure(state="normal")
        self.btn_tare.configure(state="normal")
        self.btn_stop.configure(state="disabled")

    def reset_data(self):
        self.running = False
        if self.ser: 
            try: 
                self.ser.write(b"STOP\n")
                time.sleep(0.1)
                self.ser.write(b"TARE\n")
            except: pass
            
        self.btn_start.configure(state="normal")
        self.btn_move_10.configure(state="normal")
        self.btn_tare.configure(state="normal")
        self.btn_stop.configure(state="disabled")

        self.data_x.clear()
        self.data_y.clear()
        self.data_t.clear()
        self.excel_data = {"Time (s)": [], "Force (N)": [], "Distance (mm)": [], "Stress (MPa)": [], "Strain (%)": []}
        
        self.line.set_data([], [])
        self.canvas.draw()
        
        self.card_y.configure(text="0.00")
        self.card_x.configure(text="0.00")
        self.card_t.configure(text="0.00")

    # --- EXPORTS ---
    def save_excel(self):
        if not self.excel_data["Time (s)"]:
            messagebox.showwarning("Warning", "No test data available to save!")
            return

        filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")], title="Save Data as Excel")
        if not filepath: return

        try:
            now = datetime.now()
            
            max_force = max(self.excel_data["Force (N)"]) if self.excel_data["Force (N)"] else 0
            max_stress = max(self.excel_data["Stress (MPa)"]) if self.excel_data["Stress (MPa)"] else 0
            
            meta_dict = {
                "Information": ["Test Date", "Test Time", "Test Standard", "Specimen Area (mm²)", "Initial Length (mm)", "Speed (mm/min)", "Max Force (N)", "Max Stress (MPa)"],
                "Values": [
                    now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"),
                    self.cmb_standard.get(), self.ent_area.get(), self.ent_lo.get(), self.ent_speed.get(),
                    f"{max_force:.2f}", f"{max_stress:.2f}"
                ]
            }
            df_info = pd.DataFrame(meta_dict)
            df_data = pd.DataFrame(self.excel_data)

            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df_info.to_excel(writer, sheet_name='Test Summary', index=False)
                df_data.to_excel(writer, sheet_name='Raw Data', index=False)
                
            messagebox.showinfo("Success", f"Data successfully saved to Excel!\n\nFile: {filepath}")
        except Exception as e:
            try:
                csv_path = filepath.replace(".xlsx", ".csv")
                pd.DataFrame(self.excel_data).to_csv(csv_path, index=False)
                messagebox.showinfo("Fallback Saved", f"Excel failed. Saved as CSV instead.\nPath: {csv_path}")
            except:
                messagebox.showerror("Export Error", f"Failed to save data: {str(e)}")

    def save_pdf(self):
        if not self.data_x:
            messagebox.showwarning("Warning", "No graph data available to save!")
            return
            
        filepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
        if not filepath: return

        # DÜZELTME: İzin hatası vermemesi için geçici fotoğrafı, PDF'in kaydedileceği aynı klasöre kaydediyoruz
        temp_img_path = os.path.join(os.path.dirname(filepath), "temp_plot_utm.png")

        try:
            # 1. Beyaz Temaya Çevir ve Kaydet
            self.apply_light_theme()
            self.line.set_color('#c0392b') 
            self.canvas.draw()
            
            self.fig.savefig(temp_img_path, bbox_inches='tight', dpi=150)
            
            # 2. Temayı Hemen Eski Haline Döndür
            self.apply_dark_theme()
            self.line.set_color('cyan')
            self.canvas.draw()
            
            max_force = max(self.excel_data["Force (N)"]) if self.excel_data["Force (N)"] else 0
            max_stress = max(self.excel_data["Stress (MPa)"]) if self.excel_data["Stress (MPa)"] else 0
            
            pdf = FPDF()
            pdf.add_page()
            
            pdf.set_font("Arial", 'B', 18)
            pdf.cell(0, 10, "UTM TEST REPORT", ln=True, align='C')
            pdf.ln(10)
            
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(50, 8, "Test Date & Time:")
            pdf.set_font("Arial", '', 11)
            pdf.cell(50, 8, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
            
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(50, 8, "Test Standard:")
            pdf.set_font("Arial", '', 11)
            pdf.cell(50, 8, f"{self.cmb_standard.get()}", ln=True)
            
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(50, 8, "Specimen Area:")
            pdf.set_font("Arial", '', 11)
            pdf.cell(50, 8, f"{self.ent_area.get()} mm2", ln=True)
            
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(50, 8, "Gauge Length (Lo):")
            pdf.set_font("Arial", '', 11)
            pdf.cell(50, 8, f"{self.ent_lo.get()} mm", ln=True)
            
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(50, 8, "Test Speed:")
            pdf.set_font("Arial", '', 11)
            pdf.cell(50, 8, f"{self.ent_speed.get()} mm/min", ln=True)
            
            pdf.ln(5)
            
            pdf.set_font("Arial", 'B', 12)
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(0, 10, " TEST RESULTS", ln=True, fill=True)
            pdf.ln(3)
            
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(50, 8, "Maximum Force:")
            pdf.set_font("Arial", '', 11)
            pdf.cell(50, 8, f"{max_force:.2f} N", ln=True)
            
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(50, 8, "Maximum Stress:")
            pdf.set_font("Arial", '', 11)
            pdf.cell(50, 8, f"{max_stress:.2f} MPa", ln=True)
            
            pdf.ln(5)
            
            # 3. Fotoğrafı PDF'e Ekle
            pdf.image(temp_img_path, x=10, y=105, w=190)
            
            pdf.output(filepath)
            
            # 4. Geçici Dosyayı Sil (Silinemezse programı çökertmesin diye try içine alındı)
            try:
                if os.path.exists(temp_img_path):
                    os.remove(temp_img_path)
            except:
                pass
                
            messagebox.showinfo("Success", "PDF Report saved successfully.")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            # Hata anında uygulamanın beyaz kalmasını engelle
            self.apply_dark_theme()
            self.line.set_color('cyan')
            self.canvas.draw()

    def on_closing(self):
        self.running = False
        self.stop_thread = True
        if self.ser: self.ser.close()
        self.destroy()

if __name__ == "__main__":
    app = UTMApp()
    app.mainloop()