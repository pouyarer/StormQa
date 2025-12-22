from fpdf import FPDF
import time
import os

class PDF(FPDF):
    def header(self):
        # Header Styling
        self.set_font('Helvetica', 'B', 15)
        self.set_text_color(50, 50, 200)  # StormQA Blue
        self.cell(0, 10, 'StormQA Execution Report', align='L', ln=1)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

def generate_report(test_data):
    """
    Generate a professional PDF report.
    REMOVED EMOJIS to fix font encoding error.
    """
    # ایجاد PDF
    pdf = PDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # محاسبه عرض مفید
    effective_width = pdf.epw 

    # --- 1. Executive Summary ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(0)
    pdf.cell(0, 10, "1. Executive Summary", ln=True)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    
    target_url = test_data.get('url', 'N/A')
    pdf.cell(0, 8, f"Target URL: {target_url}", ln=True)
    
    # وضعیت نهایی
    result_obj = test_data.get("test_result", {})
    if isinstance(result_obj, dict):
        status = result_obj.get("status", "UNKNOWN").upper()
    else:
        status = "UNKNOWN"
    
    if status == "PASSED":
        pdf.set_text_color(0, 150, 0)
    elif status == "FAILED":
        pdf.set_text_color(200, 0, 0)
    else:
        pdf.set_text_color(100, 100, 100)
        
    pdf.cell(0, 8, f"Final Status: {status}", ln=True)
    pdf.set_text_color(0) 
    pdf.ln(5)

    # --- 2. Key Metrics Table ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "2. Performance Metrics", ln=True)
    
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", "B", 10)
    
    col_width = effective_width / 2
    pdf.cell(col_width, 10, "Metric", 1, 0, 'C', 1)
    pdf.cell(col_width, 10, "Value", 1, 1, 'C', 1)
    
    metrics = [
        ("Total Requests", str(test_data.get('total_requests', 0))),
        ("Successful Requests", str(test_data.get('successful_requests', 0))),
        ("Failed Requests", str(test_data.get('failed_requests', 0))),
        ("Avg Latency", f"{test_data.get('avg_response_time_ms', 0):.2f} ms"),
        ("P95 Latency", f"{test_data.get('p95_latency', 0):.2f} ms"),
        ("P99 Latency", f"{test_data.get('p99_latency', 0):.2f} ms"),
        ("Throughput", f"{test_data.get('throughput_rps', 0):.2f} req/sec"),
    ]
    
    pdf.set_font("Helvetica", "", 10)
    for key, val in metrics:
        pdf.cell(col_width, 10, key, 1)
        pdf.cell(col_width, 10, val, 1, 1)
    
    pdf.ln(10)

    # --- 3. Automated Analysis ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "3. Automated Analysis & Recommendations", ln=True)
    
    pdf.set_font("Helvetica", "", 10)
    insights = []
    
    total = test_data.get('total_requests', 0)
    failed = test_data.get('failed_requests', 0)
    
    if total == 0:
        insights.append("[WARN] NO DATA: No requests were recorded. Check connection.")
    else:
        err_rate = (failed / total * 100)
        if err_rate == 0:
            insights.append("[OK] Stability: System stability is excellent. No errors detected.")
        elif err_rate < 5:
            insights.append("[WARN] Stability: Minor instability detected. Check logs for 5xx errors.")
        else:
            insights.append("[CRITICAL] Stability: High failure rate detected. Immediate review required.")

        avg_lat = test_data.get('avg_response_time_ms', 0)
        if avg_lat > 1000:
            insights.append("[SLOW] Latency: Response time is very high (>1s). Optimization needed.")
        elif avg_lat > 500:
            insights.append("[WARN] Latency: Response time is average. Consider caching.")
        else:
            insights.append("[OK] Latency: Response times are within acceptable limits.")

    if status == "FAILED" and isinstance(result_obj, dict):
         failures = result_obj.get("failures", [])
         if failures:
             insights.append("[FAIL] Threshold Violations:")
             for f in failures:
                 insights.append(f"   * {f}")

    for note in insights:
        # safe encoding just in case
        safe_note = note.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(effective_width, 8, safe_note)
        pdf.ln(1)

    # --- Save File ---
    filename = f"StormQA_Report_{int(time.time())}.pdf"
    
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    if os.path.exists(desktop_path):
        save_path = os.path.join(desktop_path, filename)
    else:
        save_path = os.path.abspath(filename)
    
    try:
        pdf.output(save_path)
        return save_path
    except Exception as e:
        fallback = f"report_{int(time.time())}.pdf"
        pdf.output(fallback)
        return os.path.abspath(fallback)