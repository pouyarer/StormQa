import customtkinter as ctk
import os
import threading
import asyncio
import webbrowser
import json
import shlex 
from PIL import Image
from datetime import datetime
from tkinter import messagebox
from pathlib import Path

try:
    from stormqa.core.loader import LoadTestEngine
    from stormqa.core.network_sim import run_network_check, NETWORK_PROFILES
    from stormqa.core.db_sim import run_smart_db_test
    from stormqa.reporters.main_reporter import generate_report
except ImportError:
    pass

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

C_BG = "#1a1a1a"         
C_SIDEBAR = "#101010"    
C_ACCENT = "#1f6aa5"     
C_RED = "#c0392b"        
C_GREEN = "#27ae60"      
C_TEXT = "#ecf0f1"
C_NEON = "#00FFFF"       
C_GOLD = "#FFD700"

# --- CURL PARSER ENGINE (NEW) ---
class CurlParser:
    @staticmethod
    def parse(curl_command):
        
        clean_cmd = curl_command.replace('curl ', '', 1).strip()
        try:
            tokens = shlex.split(clean_cmd)
        except Exception as e:
            return None, f"Parse Error: {e}"

        parsed = {
            "method": "GET",
            "url": "",
            "headers": {},
            "body": None
        }

        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            if token.startswith('http'):
                parsed["url"] = token
                i += 1
            
            elif token in ('-X', '--request'):
                parsed["method"] = tokens[i+1].upper()
                i += 2
            
            elif token in ('-H', '--header'):
                header_str = tokens[i+1]
                if ':' in header_str:
                    key, value = header_str.split(':', 1)
                    parsed["headers"][key.strip()] = value.strip()
                i += 2
            
            elif token in ('-b', '--cookie'):
                parsed["headers"]["Cookie"] = tokens[i+1]
                i += 2
                
            elif token in ('-d', '--data', '--data-raw', '--data-binary'):
                parsed["body"] = tokens[i+1]
                if parsed["method"] == "GET": parsed["method"] = "POST"
                i += 2
                
            elif token == '--compressed':
                i += 1
            elif token.startswith('-'):
                i += 2
            else:
                if not parsed["url"] and token.startswith('http'):
                    parsed["url"] = token
                i += 1
                
        return parsed, None

# --- CyberChart ---
class CyberChart(ctk.CTkCanvas):
    def __init__(self, master, width=800, height=250, line_color=C_NEON):
        super().__init__(master, width=width, height=height, bg="#151515", highlightthickness=0)
        self.line_color = line_color
        self.data = [0] * 100 
        self.height = height
        self.width = width

    def update_data(self, new_val):
        self.data.append(new_val)
        if len(self.data) > 80: self.data.pop(0)
        self.redraw()

    def redraw(self):
        self.delete("all")
        for i in range(0, self.height, 40):
            self.create_line(0, i, self.width, i, fill="#222", width=1)
        max_val = max(self.data) if max(self.data) > 5 else 10
        points = []
        step_x = self.width / (len(self.data) - 1) if len(self.data) > 1 else 0
        for i, val in enumerate(self.data):
            x = i * step_x
            normalized_h = (val / max_val)
            y = self.height - (normalized_h * (self.height - 30)) - 15 
            points.append(x); points.append(y)
        if len(points) >= 4:
            poly = points.copy(); poly.extend([self.width, self.height, 0, self.height])
            self.create_polygon(poly, fill=self.line_color, outline="", stipple="gray25") 
            self.create_line(points, fill=self.line_color, width=2, capstyle="round", smooth=True)
            lx, ly = points[-2], points[-1]
            self.create_oval(lx-3, ly-3, lx+3, ly+3, fill="white", outline=self.line_color)

# --- APP ---
class StormQaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("StormQA A zero-config, powerful tool for Load, Network, and DB testing v2.1")
        self.geometry("1280x950") 
        
        self.grid_columnconfigure(0, weight=0) 
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        try:
            self.engine = LoadTestEngine()
        except:
            self.engine = None 
            
        self.running = False
        self.steps_ui = [] 
        self.test_results_cache = {} 

        self._init_sidebar()
        self._init_content_area() 
        self._init_terminal()
        self.tabs.set("Load Scenario")

    def _init_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color=C_SIDEBAR)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1) 
        
        # --- LOGO SECTION (FIXED PATH) ---
        try:
            # پیدا کردن مسیر دقیق فایلی که الان باز است
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # چسباندن نام عکس به آن مسیر
            img_path = os.path.join(current_dir, "storm_logo.png")
            
            pil_img = Image.open(img_path)
            
            # تنظیم سایز (عرض، ارتفاع) - این را بسته به شکل لوگویت تنظیم کن
            my_logo = ctk.CTkImage(light_image=pil_img, 
                                   dark_image=pil_img, 
                                   size=(100, 70))
            
            ctk.CTkLabel(self.sidebar, text="", image=my_logo).pack(pady=(40, 5))
            
        except Exception as e:
            # چاپ خطای دقیق‌تر برای دیباگ
            print(f"Logo Error: {e}")
            ctk.CTkLabel(self.sidebar, text="STORM QA", font=("Impact", 35), text_color=C_NEON).pack(pady=(40, 5))
        # ---------------------------------

        ctk.CTkLabel(self.sidebar, text="V2.1", font=("Arial", 10, "bold"), text_color="gray").pack(pady=(0, 20))

        self.stat_users = self._create_stat_widget("ACTIVE USERS", "0")
        self.stat_rps = self._create_stat_widget("RPS (Req/s)", "0.0")
        self.stat_lat = self._create_stat_widget("LATENCY (ms)", "0")
        self.stat_fail = self._create_stat_widget("ERRORS", "0", color=C_RED)

        ctk.CTkFrame(self.sidebar, height=2, fg_color="#222").pack(fill="x", pady=20, padx=20)

        self.btn_donate = ctk.CTkButton(self.sidebar, 
                                        text="❤  Donate & Support", 
                                        font=("Arial", 11, "bold"),
                                        height=32,
                                        width=160,
                                        corner_radius=20,
                                        fg_color="transparent",
                                        border_width=2,
                                        border_color=C_GOLD,
                                        text_color=C_GOLD,
                                        hover_color="#333",
                                        cursor="hand2",
                                        command=lambda: webbrowser.open("https://pay.oxapay.com/14009511/156840325"))
        self.btn_donate.pack(pady=10)

        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.pack(side="bottom", pady=20)
        ctk.CTkLabel(footer, text="Powered by Testeto", font=("Arial", 10), text_color="gray").pack()
        link = ctk.CTkLabel(footer, text="Pouya Rezapour", font=("Arial", 11, "underline"), text_color=C_ACCENT, cursor="hand2")
        link.pack()
        link.bind("<Button-1>", lambda e: webbrowser.open("https://pouyarezapour.ir"))

    def _create_stat_widget(self, title, value, color=C_TEXT):
        f = ctk.CTkFrame(self.sidebar, fg_color="#151515", corner_radius=6)
        f.pack(fill="x", padx=15, pady=6)
        ctk.CTkLabel(f, text=title, font=("Arial", 9, "bold"), text_color="gray", anchor="w").pack(fill="x", padx=10, pady=(6, 0))
        lbl = ctk.CTkLabel(f, text=value, font=("Consolas", 22, "bold"), text_color=color, anchor="w")
        lbl.pack(fill="x", padx=10, pady=(0, 6))
        return lbl

    def _init_content_area(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.tabs = ctk.CTkTabview(self.main_frame, fg_color="transparent")
        self.tabs.pack(fill="both", expand=True)
        self.tabs._segmented_button.pack_forget() 

        self.tab_load = self.tabs.add("Load Scenario")
        self.tab_net = self.tabs.add("Network Sim")
        self.tab_db = self.tabs.add("Database")
        
        self._build_load_ui()
        self._build_net_ui()
        self._build_db_ui()

    def _init_terminal(self):
        term_frame = ctk.CTkFrame(self, height=150, fg_color="#000000", corner_radius=0)
        term_frame.grid(row=1, column=1, sticky="ew", padx=0, pady=0)
        head = ctk.CTkFrame(term_frame, height=25, fg_color="#222", corner_radius=0)
        head.pack(fill="x")
        ctk.CTkLabel(head, text="SYSTEM TERMINAL", font=("Consolas", 10, "bold"), text_color="gray").pack(side="left", padx=10)
        ctk.CTkButton(head, text="CLEAR", width=50, height=18, fg_color="#333", command=lambda: self.console.delete("0.0", "end")).pack(side="right", padx=5)
        self.console = ctk.CTkTextbox(term_frame, height=125, font=("Consolas", 11), text_color=C_GREEN, fg_color="transparent")
        self.console.pack(fill="both", expand=True, padx=5, pady=5)
        self.log("StormQA v2.2 Ready.")

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.console.insert("end", f"[{ts}] > {msg}\n")
        self.console.see("end")

    # ================= LOAD UI (UPDATED WITH CURL) =================
    def _build_load_ui(self):
        scroll = ctk.CTkScrollableFrame(self.tab_load, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # 1. Target & Method & CURL Button
        card_conf = ctk.CTkFrame(scroll, fg_color=C_SIDEBAR)
        card_conf.pack(fill="x", pady=5)
        
        top_row = ctk.CTkFrame(card_conf, fg_color="transparent")
        top_row.pack(fill="x", padx=15, pady=(15, 5))
        
        ctk.CTkLabel(top_row, text="METHOD & TARGET:", font=("Arial", 11, "bold"), text_color="gray").pack(side="left")
        
        # --- CURL BUTTON (NEW) ---
        ctk.CTkButton(top_row, text="📋 Import cURL", width=100, height=24, 
                      fg_color="#333", hover_color="#444", font=("Arial", 11),
                      command=self._open_curl_import).pack(side="right")
        # -------------------------

        input_row = ctk.CTkFrame(card_conf, fg_color="transparent")
        input_row.pack(fill="x", padx=10, pady=(0, 15))

        self.method_var = ctk.StringVar(value="GET")
        self.method_menu = ctk.CTkOptionMenu(input_row, values=["GET", "POST", "PUT", "DELETE"], variable=self.method_var, width=100)
        self.method_menu.pack(side="left", padx=5)

        self.url_entry = ctk.CTkEntry(input_row, placeholder_text="https://api.example.com/login", width=400, border_color="#333")
        self.url_entry.pack(side="left", padx=5, expand=True, fill="x")

        # 2. Advanced Config
        self.adv_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.adv_frame.pack(fill="x", pady=5)
        
        self.adv_toggle = ctk.CTkSwitch(self.adv_frame, text="Advanced Config (Headers/Body/Auth)", command=self._toggle_advanced)
        self.adv_toggle.pack(anchor="w", padx=20)
        
        self.adv_box = ctk.CTkFrame(self.adv_frame, fg_color=C_SIDEBAR)
        
        ctk.CTkLabel(self.adv_box, text="HEADERS (JSON format):").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.headers_input = ctk.CTkTextbox(self.adv_box, height=80, border_color="#444", font=("Consolas", 11))
        self.headers_input.insert("0.0", '{"Content-Type": "application/json"}')
        self.headers_input.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.adv_box, text="BODY (JSON format):").grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.body_input = ctk.CTkTextbox(self.adv_box, height=80, border_color="#444", font=("Consolas", 11))
        self.body_input.insert("0.0", '') 
        self.body_input.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(self.adv_box, text="ASSERTION (Response MUST contain):").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.assert_input = ctk.CTkEntry(self.adv_box, placeholder_text="e.g. success or token", width=300)
        self.assert_input.grid(row=3, column=0, padx=10, pady=5, sticky="w")

        self.adv_box.grid_columnconfigure(0, weight=1)
        self.adv_box.grid_columnconfigure(1, weight=1)

        # 3. Chart
        chart_frame = ctk.CTkFrame(scroll, fg_color=C_SIDEBAR)
        chart_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(chart_frame, text="REAL-TIME TRAFFIC", font=("Arial", 11, "bold"), text_color=C_NEON).pack(side="left", padx=10)
        self.chart = CyberChart(chart_frame, height=200, width=800)
        self.chart.pack(fill="x", padx=10, pady=(0, 10))

        # 4. Scenario
        frame_steps = ctk.CTkFrame(scroll, fg_color=C_SIDEBAR)
        frame_steps.pack(fill="x", pady=5)
        h = ctk.CTkFrame(frame_steps, fg_color="transparent")
        h.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(h, text="SCENARIO CONFIG", font=("Arial", 12, "bold"), text_color="white").pack(side="left")
        ctk.CTkButton(h, text="+ Add Step", width=80, height=25, fg_color="#333", command=self._add_step).pack(side="right")

        self.steps_box = ctk.CTkFrame(frame_steps, fg_color="transparent")
        self.steps_box.pack(fill="x", padx=10, pady=5)
        cols = ctk.CTkFrame(self.steps_box, fg_color="#222", height=25)
        cols.pack(fill="x")
        for t, w in [("#", 30), ("Users", 80), ("Duration", 80), ("Ramp", 80), ("Think", 80)]:
            ctk.CTkLabel(cols, text=t, width=w, font=("Arial", 10, "bold"), text_color="gray").pack(side="left", padx=5)
        self._add_step() 

        # 5. Control
        ctrl = ctk.CTkFrame(scroll, fg_color="transparent")
        ctrl.pack(fill="x", pady=20)
        self.btn_start = ctk.CTkButton(ctrl, text="START STORM ⚡️", height=50, font=("Arial", 15, "bold"),
                                       fg_color=C_ACCENT, text_color="black", hover_color="#154c79", command=self.toggle_test)
        self.btn_start.pack(fill="x")
        self.btn_pdf = ctk.CTkButton(ctrl, text="DOWNLOAD REPORT", state="disabled", fg_color="#222", command=self._export_pdf)
        self.btn_pdf.pack(fill="x", pady=5)

    def _toggle_advanced(self):
        if self.adv_toggle.get() == 1:
            self.adv_box.pack(fill="x", padx=20, pady=5)
        else:
            self.adv_box.pack_forget()

    # --- CURL POPUP LOGIC (NEW) ---
    def _open_curl_import(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Import from cURL")
        dialog.geometry("600x400")
        dialog.attributes("-topmost", True) 
        
        ctk.CTkLabel(dialog, text="Paste your cURL command here:", font=("Arial", 12, "bold")).pack(pady=10)
        
        txt_curl = ctk.CTkTextbox(dialog, height=250, border_color=C_ACCENT, border_width=1)
        txt_curl.pack(fill="both", expand=True, padx=20, pady=5)
        
        def process_curl():
            raw_curl = txt_curl.get("0.0", "end").strip()
            if not raw_curl: return
            
            parsed_data, error = CurlParser.parse(raw_curl)
            
            if error:
                messagebox.showerror("Parse Error", error)
                return
            
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, parsed_data["url"])
            
            self.method_var.set(parsed_data["method"])
            
            if self.adv_toggle.get() == 0:
                self.adv_toggle.select()
                self._toggle_advanced()
            
            self.headers_input.delete("0.0", "end")
            self.headers_input.insert("0.0", json.dumps(parsed_data["headers"], indent=2))
            
            self.body_input.delete("0.0", "end")
            if parsed_data["body"]:
                try:
                    b_json = json.loads(parsed_data["body"])
                    self.body_input.insert("0.0", json.dumps(b_json, indent=2))
                except:
                    self.body_input.insert("0.0", parsed_data["body"])
            
            self.log("✅ cURL imported successfully!")
            dialog.destroy()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10, padx=20)
        ctk.CTkButton(btn_frame, text="Import & Parse", fg_color=C_GREEN, command=process_curl).pack(side="right")
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="#333", command=dialog.destroy).pack(side="left")

    def _add_step(self):
        row = ctk.CTkFrame(self.steps_box, fg_color="transparent"); row.pack(fill="x", pady=2)
        idx = len(self.steps_ui) + 1
        lbl = ctk.CTkLabel(row, text=f"{idx}", width=30); lbl.pack(side="left")
        def ent(v):
            e = ctk.CTkEntry(row, width=80, border_color="#333", justify="center")
            e.insert(0, v); e.pack(side="left", padx=5)
            return e
        vals = {"u": ent("10"), "d": ent("30"), "r": ent("5"), "t": ent("0.5")}
        ctk.CTkButton(row, text="×", width=30, fg_color="#222", hover_color=C_RED, command=lambda: self._del_step(row)).pack(side="right", padx=5)
        self.steps_ui.append({"frame": row, "lbl": lbl, **vals})

    def _del_step(self, frame):
        for s in self.steps_ui:
            if s["frame"] == frame: self.steps_ui.remove(s); break
        frame.destroy()
        for i, s in enumerate(self.steps_ui): s["lbl"].configure(text=str(i+1))

    # ================= LOGIC =================
    def toggle_test(self):
        if not self.running:
            raw = self.url_entry.get().strip()
            if not raw: return messagebox.showerror("Err", "Target required")
            url = f"http://{raw}" if not raw.startswith("http") else raw

            method = self.method_var.get()
            headers = None
            body = None
            assertion = None

            if self.adv_toggle.get() == 1:
                try:
                    h_txt = self.headers_input.get("0.0", "end").strip()
                    if h_txt: headers = json.loads(h_txt)
                    b_txt = self.body_input.get("0.0", "end").strip()
                    if b_txt: 
                        try: body = json.loads(b_txt)
                        except: body = b_txt 
                    a_txt = self.assert_input.get().strip()
                    if a_txt: assertion = a_txt
                except json.JSONDecodeError as e:
                    return messagebox.showerror("Error", f"Invalid JSON format: {e}")

            steps = []
            try:
                for s in self.steps_ui:
                    steps.append({
                        "users": int(s["u"].get()), "duration": int(s["d"].get()),
                        "ramp": int(s["r"].get()), "think": float(s["t"].get())
                    })
            except: return messagebox.showerror("Err", "Invalid inputs")
            if not steps: return messagebox.showerror("Err", "Add steps")

            self.running = True
            self.btn_start.configure(text="ABORT OPERATION", fg_color=C_RED, text_color="white")
            self.btn_pdf.configure(state="disabled")
            
            self.chart.data = [0]*100; self.chart.redraw()
            self._update_sidebar_stats(0, 0, 0, 0)
            
            self.log(f"Locked: {method} {url}")
            if assertion: self.log(f"Assert: '{assertion}'")
            
            threading.Thread(target=self._run, args=(url, steps, method, headers, body, assertion), daemon=True).start()
        else:
            self.running = False
            if self.engine: self.engine._stop_event.set()
            self.log("Aborting...")

    def _run(self, url, steps, method, headers, body, assertion):
        if not self.engine: return
        try:
            res = asyncio.run(self.engine.start_scenario(
                url, steps, self._update_monitor, 
                method=method, headers=headers, body=body, assertion=assertion
            ))
            self.test_results_cache["Load Test"] = res
            self.after(0, self._finish, res)
        except Exception as e:
            self.log(f"Error: {e}")
            self.running = False
            self.after(0, self._reset_ui)

    def _update_monitor(self, stats):
        self.after(0, lambda: self._ui_update(stats))

    def _ui_update(self, stats):
        self.chart.update_data(stats['users'])
        self._update_sidebar_stats(stats['users'], f"{stats['rps']:.1f}", f"{stats['avg_latency']:.0f} ms", stats['failed'])
        if int(stats['rps']) % 10 == 0: self.log(f"Load: {stats['users']} users | {stats['rps']:.1f} rps")

    def _update_sidebar_stats(self, u, r, l, f):
        self.stat_users.configure(text=str(u))
        self.stat_rps.configure(text=str(r))
        self.stat_lat.configure(text=str(l))
        self.stat_fail.configure(text=str(f))

    def _finish(self, res):
        self._reset_ui()
        self.log(f"Done. Failures: {res['failed_requests']}")
        messagebox.showinfo("Done", "Finished.")

    def _reset_ui(self):
        self.running = False
        self.btn_start.configure(text="START STORM ⚡️", fg_color=C_ACCENT, text_color="black")
        self.btn_pdf.configure(state="normal")

    def _export_pdf(self):
        if not self.test_results_cache: return
        try:
            path = generate_report(self.test_results_cache)
            if "Error" in path: messagebox.showerror("Err", path)
            else: 
                self.log(f"Exported: {path}")
                messagebox.showinfo("Saved", f"PDF at: {path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _build_net_ui(self):
        f = ctk.CTkFrame(self.tab_net, fg_color="transparent")
        f.pack(fill="both", padx=50, pady=50)
        ctk.CTkLabel(f, text="NETWORK DIAGNOSTICS", font=("Impact", 24), text_color="#555").pack(pady=20)
        self.n_u = ctk.CTkEntry(f, width=400, placeholder_text="Target URL"); self.n_u.pack(pady=10)
        self.n_p = ctk.CTkOptionMenu(f, values=list(NETWORK_PROFILES.keys())); self.n_p.pack(pady=10)
        ctk.CTkButton(f, text="RUN PING/TRACE", width=200, height=45, fg_color=C_ACCENT, text_color="black", command=self._run_net).pack(pady=30)
        self.n_l = ctk.CTkLabel(f, text="Status: Ready", font=("Consolas", 12)); self.n_l.pack()

    def _run_net(self):
        u = self.n_u.get()
        if not u: return
        if not u.startswith("http"): u = f"http://{u}"
        self.log(f"Network Check: {u}")
        res = asyncio.run(run_network_check(u, self.n_p.get()))
        self.test_results_cache["Network"] = res
        if res.get('status') == 'success':
            d = res.get('simulated_delay', 0)
            c = C_GREEN if d < 500 else ("#F1C40F" if d < 1000 else C_RED)
            m = f"Connected | Latency: {d}ms"
        else: m = f"Failed: {res.get('message')}"; c = C_RED
        self.n_l.configure(text=m, text_color=c)

    def _build_db_ui(self):
        f = ctk.CTkFrame(self.tab_db, fg_color="transparent")
        f.pack(fill="both", padx=20, pady=20)
        self.d_u = ctk.CTkEntry(f, width=400, placeholder_text="DB API Endpoint"); self.d_u.pack(pady=20)
        r = ctk.CTkFrame(f, fg_color="transparent"); r.pack(pady=10)
        ctk.CTkButton(r, text="DISCOVER", width=150, command=lambda: self._run_db("discovery")).pack(side="left", padx=10)
        ctk.CTkButton(r, text="FLOOD", width=150, fg_color=C_RED, command=lambda: self._run_db("connection_flood")).pack(side="left", padx=10)
        self.d_out = ctk.CTkTextbox(f, height=200); self.d_out.pack(fill="both", pady=20)

    def _run_db(self, m):
        u = self.d_u.get()
        if not u: return
        if not u.startswith("http"): u = f"http://{u}"
        self.log(f"DB {m}...")
        res = asyncio.run(run_smart_db_test(u, m))
        self.test_results_cache["DB"] = res
        self.d_out.delete("0.0", "end"); self.d_out.insert("0.0", str(res))

def launch():
    app = StormQaApp()
    app.mainloop()

if __name__ == "__main__":
    launch()