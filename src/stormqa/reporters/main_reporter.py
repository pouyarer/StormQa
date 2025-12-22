from fpdf import FPDF
import time
import os

class PDF(FPDF):
    def header(self):
        # Header Styling
        self.set_font('Helvetica', 'B', 15)
        self.set_text_color(50, 50, 200) # Blue Title
        self.cell(0, 10, 'StormQA Execution Report', align='L', ln=1)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

def generate_report(test_data):
    """
    Generate a professional PDF report from test results.
    """
    pdf = PDF()
    pdf.add_page()
    
    # 1. Executive Summary
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(0)
    pdf.cell(0, 10, "1. Executive Summary", ln=True)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.cell(0, 8, f"Target URL: {test_data.get('url', 'N/A')}", ln=True)
    
    # Status Badge Logic
    status = "UNKNOWN"
    if "test_result" in test_data:
        status = test_data["test_result"].get("status", "UNKNOWN").upper()
    
    pdf.set_text_color(0, 150, 0) if status == "PASSED" else pdf.set_text_color(200, 0, 0)
    pdf.cell(0, 8, f"Final Status: {status}", ln=True)
    pdf.set_text_color(0) # Reset color
    pdf.ln(5)

    # 2. Key Metrics Table
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "2. Performance Metrics", ln=True)
    
    # Table Header
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(50, 10, "Metric", 1, 0, 'C', 1)
    pdf.cell(50, 10, "Value", 1, 1, 'C', 1)
    
    # Table Rows
    metrics = [
        ("Total Requests", str(test_data.get('total_requests', 0))),
        ("Failed Requests", str(test_data.get('failed_requests', 0))),
        ("Avg Latency", f"{test_data.get('avg_response_time_ms', 0):.2f} ms"),
        ("P95 Latency", f"{test_data.get('p95_latency', 0):.2f} ms"),
        ("P99 Latency", f"{test_data.get('p99_latency', 0):.2f} ms"),
        ("Throughput", f"{test_data.get('throughput_rps', 0):.2f} req/sec"),
    ]
    
    pdf.set_font("Helvetica", "", 10)
    for key, val in metrics:
        pdf.cell(50, 10, key, 1)
        pdf.cell(50, 10, val, 1, 1)
    
    pdf.ln(10)

    # 3. Automated Analysis (AI Insight Simulation)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "3. Automated Analysis & Recommendations", ln=True)
    
    pdf.set_font("Helvetica", "", 10)
    insights = []
    
    # Logic for insights
    err_rate = 0
    if test_data.get('total_requests', 0) > 0:
        err_rate = (test_data.get('failed_requests', 0) / test_data.get('total_requests', 1)) * 100
    
    if err_rate == 0:
        insights.append("✅ System stability is excellent. No errors detected.")
    elif err_rate < 5:
        insights.append("⚠️ Minor instability detected. Check server logs for 5xx errors.")
    else:
        insights.append("🔥 CRITICAL: High failure rate detected. Immediate infrastructure review required.")

    if test_data.get('avg_response_time_ms', 0) > 500:
        insights.append("🐢 Latency is high (>500ms). Consider optimizing database queries or adding cache.")
    else:
        insights.append("⚡ Response times are within acceptable limits.")

    if status == "FAILED":
         if "test_result" in test_data and "failures" in test_data["test_result"]:
             insights.append("⛔ Threshold Violations:")
             for f in test_data["test_result"]["failures"]:
                 insights.append(f"   - {f}")

    for note in insights:
        pdf.multi_cell(0, 8, note)

    # Save File
    filename = f"StormQA_Report_{int(time.time())}.pdf"
    
    # Get user Desktop or Documents path (Cross-platform)
    save_path = os.path.join(os.path.expanduser("~"), "Desktop", filename)
    
    try:
        pdf.output(save_path)
        return save_path
    except Exception as e:
        # Fallback to current dir if desktop write fails
        pdf.output(filename)
        return os.path.abspath(filename)