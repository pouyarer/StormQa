import json
from fpdf import FPDF
from datetime import datetime
from pathlib import Path
import os
import platform

class PDFReport(FPDF):
    def header(self):
        self.set_fill_color(30, 30, 30) 
        self.rect(0, 0, 210, 35, 'F')
        self.set_font('Arial', 'B', 18)
        self.set_text_color(255, 255, 255)
        self.cell(0, 15, 'StormQA v2.0 Report', 0, 1, 'C')
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_report(data: dict) -> str:

    if platform.system() == "Windows":
        download_dir = str(Path.home() / "Downloads")
    else:
        download_dir = str(Path.home() / "Downloads")
        
    filename = f"StormQA_Report_{datetime.now().strftime('%H%M%S')}.pdf"
    full_path = os.path.join(download_dir, filename)

    pdf = PDFReport()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1)
    pdf.ln(5)

    for test_name, metrics in data.items():
        pdf.set_font("Arial", "B", 14)
        pdf.set_fill_color(220, 220, 220)
        pdf.cell(0, 10, f" {test_name}", 1, 1, 'L', fill=True)
        
        pdf.set_font("Arial", "", 11)
        if isinstance(metrics, dict):
            for key, value in metrics.items():
                k = str(key).replace("_", " ").title()
                v = str(value)
                if isinstance(value, float): v = f"{value:.2f}"
                
                pdf.cell(100, 8, k, 1)
                pdf.cell(90, 8, v, 1, 1)
        pdf.ln(8)

    try:
        pdf.output(full_path)
        return full_path
    except Exception as e:
        return f"Error: {str(e)}"