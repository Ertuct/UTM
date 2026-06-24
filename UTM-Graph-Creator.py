import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import customtkinter as ctk
from tkinter import filedialog, messagebox
from fpdf import FPDF
import os
from datetime import datetime

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class UTMDataViewer(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.geometry("1000x750")
        self.title("UTM Data Viewer & Graph Cleaner")
        
        self.df = None
        self.raw_x = []
        self.raw_y = []
        
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ÜST PANEL - Dosya Yükleme
        self.fr_top = ctk.CTkFrame(self)
        self.fr_top.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.btn_load = ctk.CTkButton(self.fr_top, text="LOAD EXCEL DATA", font=("Arial", 14, "bold"), command=self.load_excel)
        self.btn_load.pack(side="left", padx=10, pady=10)
        
        self.lbl_file = ctk.CTkLabel(self.fr_top, text="No file loaded.", text_color="gray")
        self.lbl_file.pack(side="left", padx=10, pady=10)

        self.btn_pdf = ctk.CTkButton(self.fr_top, text="EXPORT CLEAN PDF", fg_color="#d35400", state="disabled", command=self.save_pdf)
        self.btn_pdf.pack(side="right", padx=10, pady=10)

        # ORTA PANEL - Grafik
        self.fr_graph = ctk.CTkFrame(self, fg_color="transparent")
        self.fr_graph.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        self.fig, self.ax = plt.subplots(figsize=(8, 5), dpi=100)
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
        
        self.line, = self.ax.plot([], [], color='cyan', linewidth=2)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.fr_graph)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # ALT PANEL - Kırpma (Trim) Kontrolleri
        self.fr_bottom = ctk.CTkFrame(self)
        self.fr_bottom.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(self.fr_bottom, text="DATA TRIMMING (Temizleme Araçları)", font=("Arial", 14, "bold")).pack(pady=5)
        
        # Başlangıç Kırpma
        self.lbl_start = ctk.CTkLabel(self.fr_bottom, text="Trim Start: 0 points")
        self.lbl_start.pack()
        self.slider_start = ctk.CTkSlider(self.fr_bottom, from_=0, to=100, command=self.update_graph)
        self.slider_start.set(0)
        self.slider_start.pack(fill="x", padx=20, pady=5)
        
        # Bitiş Kırpma
        self.lbl_end = ctk.CTkLabel(self.fr_bottom, text="Trim End: 0 points")
        self.lbl_end.pack()
        self.slider_end = ctk.CTkSlider(self.fr_bottom, from_=0, to=100, command=self.update_graph)
        self.slider_end.set(0)
        self.slider_end.pack(fill="x", padx=20, pady=10)

    def load_excel(self):
        filepath = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
        if not filepath: return
        
        try:
            # Excel'den "Raw Data" sayfasını oku
            self.df = pd.read_excel(filepath, sheet_name="Raw Data")
            
            if "Strain (%)" not in self.df.columns or "Stress (MPa)" not in self.df.columns:
                messagebox.showerror("Error", "Bozuk veya uyumsuz Excel dosyası. Sütunlar bulunamadı.")
                return
                
            self.raw_x = self.df["Strain (%)"].tolist()
            self.raw_y = self.df["Stress (MPa)"].tolist()
            
            # Slider sınırlarını veri sayısına göre ayarla
            max_points = len(self.raw_x)
            self.slider_start.configure(to=max_points - 2) # En az 2 nokta kalsın
            self.slider_end.configure(to=max_points - 2)
            
            self.slider_start.set(0)
            self.slider_end.set(0)
            
            self.lbl_file.configure(text=os.path.basename(filepath))
            self.btn_pdf.configure(state="normal")
            
            self.update_graph()
            
        except Exception as e:
            messagebox.showerror("Error", f"Dosya okunamadı:\n{e}")

    def update_graph(self, value=None):
        if not self.raw_x: return
        
        total_points = len(self.raw_x)
        cut_start = int(self.slider_start.get())
        cut_end = int(self.slider_end.get())
        
        self.lbl_start.configure(text=f"Trim Start: {cut_start} points removed")
        self.lbl_end.configure(text=f"Trim End: {cut_end} points removed")
        
        # Mantıksal sınır kontrolü (Kırpmalar birbirini geçmesin)
        if cut_start + cut_end >= total_points:
            return
            
        # Verileri kırp
        clean_x = self.raw_x[cut_start : total_points - cut_end]
        clean_y = self.raw_y[cut_start : total_points - cut_end]
        
        # Eksiye düşen değerleri (TARE sapmalarını) sıfırla
        clean_y = [max(0, val) for val in clean_y]
        
        # Çiz
        self.line.set_data(clean_x, clean_y)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

        # Güncel verileri PDF için kaydet
        self.clean_x = clean_x
        self.clean_y = clean_y

    def save_pdf(self):
        if not hasattr(self, 'clean_x') or not self.clean_x: return
        
        filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
        if not filename: return
        
        temp_img_path = os.path.join(os.path.dirname(filename), "recovered_plot.png")
        
        try:
            # Beyaz tema
            self.fig.patch.set_facecolor('white')
            self.ax.set_facecolor('white')
            self.ax.tick_params(colors='black')
            self.ax.spines['bottom'].set_color('black')
            self.ax.spines['top'].set_color('black') 
            self.ax.spines['right'].set_color('black')
            self.ax.spines['left'].set_color('black')
            self.ax.xaxis.label.set_color('black')
            self.ax.yaxis.label.set_color('black')
            self.line.set_color('#c0392b') 
            self.canvas.draw()
            
            self.fig.savefig(temp_img_path, bbox_inches='tight', dpi=150)
            
            # Siyah temaya geri dön
            self.fig.patch.set_facecolor('#2b2b2b')
            self.ax.set_facecolor('#2b2b2b')
            self.ax.tick_params(colors='white')
            self.ax.spines['bottom'].set_color('white')
            self.ax.spines['top'].set_color('white') 
            self.ax.spines['right'].set_color('white')
            self.ax.spines['left'].set_color('white')
            self.ax.xaxis.label.set_color('white')
            self.ax.yaxis.label.set_color('white')
            self.line.set_color('cyan')
            self.canvas.draw()
            
            max_stress = max(self.clean_y)
            max_strain = max(self.clean_x)
            
            pdf = FPDF()
            pdf.add_page()
            
            pdf.set_font("Arial", 'B', 18)
            pdf.cell(0, 10, "RECOVERED UTM TEST REPORT", ln=True, align='C')
            pdf.ln(10)
            
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(50, 8, "Recovery Date:")
            pdf.set_font("Arial", '', 11)
            pdf.cell(50, 8, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
            
            pdf.ln(5)
            
            pdf.set_font("Arial", 'B', 12)
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(0, 10, " RECOVERED RESULTS", ln=True, fill=True)
            pdf.ln(3)
            
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(50, 8, "Maximum Stress:")
            pdf.set_font("Arial", '', 11)
            pdf.cell(50, 8, f"{max_stress:.2f} MPa", ln=True)
            
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(50, 8, "Strain at Break/End:")
            pdf.set_font("Arial", '', 11)
            pdf.cell(50, 8, f"{max_strain:.2f} %", ln=True)
            
            pdf.ln(5)
            pdf.image(temp_img_path, x=10, y=90, w=190)
            
            pdf.output(filename)
            try:
                os.remove(temp_img_path)
            except: pass
            
            messagebox.showinfo("Success", "Temizlenmiş grafik başarıyla PDF olarak kaydedildi!")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    app = UTMDataViewer()
    app.mainloop()