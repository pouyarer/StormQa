import json
import csv
from fpdf import FPDF
from typing import Dict, Any
import time

def _generate_pdf(data: Dict[str, Any], filename: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    pdf.cell(0, 10, "StormQA Test Report", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
    pdf.ln(10)

    for test_type, metrics in data.items():
        if isinstance(metrics, dict):
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, f"--- {test_type} Results ---", ln=True)
            pdf.set_font("Arial", "", 10)
            for key, value in metrics.items():
                if isinstance(value, float):
                    value = f"{value:.2f}"
                pdf.cell(0, 8, f"  - {key}: {value}", ln=True)
            pdf.ln(5)
            
    pdf.output(filename)

def generate_report(data: Dict[str, Any], file_path: str) -> str:
    """Generates the final report based on the given file path and format."""
    
    format_type = file_path.split('.')[-1].lower()

    try:
        if format_type == "json":
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)
        
        elif format_type == "csv":
            with open(file_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["TestType", "Metric", "Value"])
                for test_type, metrics in data.items():
                    if isinstance(metrics, dict):
                        for key, value in metrics.items():
                            writer.writerow([test_type, key, value])
        
        elif format_type == "pdf":
            _generate_pdf(data, file_path)
            
        else:
            return f"❌ Error: Unsupported format '{format_type}'."
            
        return f"✅ Report successfully generated and saved to {file_path}"
    except Exception as e:
        return f"❌ Error generating report: {e}"
