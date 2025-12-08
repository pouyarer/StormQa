import customtkinter as ctk
import threading
import asyncio
import webbrowser
from datetime import datetime
from tkinter import messagebox
from pathlib import Path

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from stormqa.core.loader import LoadTestEngine
from stormqa.core.network_sim import run_network_check, NETWORK_PROFILES
from stormqa.core.db_sim import run_smart_db_test
from stormqa.reporters.main_reporter import generate_report

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

C_BG = "#1a1a1a"         
C_SIDEBAR = "#101010"    
C_ACCENT = "#1f6aa5"     
C_RED = "#c0392b"        
C_GREEN = "#27ae60"      
C_TEXT = "#ecf0f1"
C_NEON = "#00FFFF" 

class StormQaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("StormQA A zero-config, powerful tool for Load, Network, and DB testing.")
        self.geometry("1280x900")
        
        self.grid_columnconfigure(0, weight=0) 
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.engine = LoadTestEngine()
        self.running = False
        self.steps_ui = [] 
        self.test_results_cache = {} 

        self._init_sidebar()
        self._init_content_area() 
        self._init_terminal()

    def _init_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=C_SIDEBAR)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1) 
        
        ctk.CTkLabel(self.sidebar, text="STORM QA", font=("Impact", 30), text_color=C_NEON).grid(row=0, column=0, padx=20, pady=(40, 5))
        ctk.CTkLabel(self.sidebar, text="v2.0", font=("Arial", 11), text_color="gray").grid(row=1, column=0, pady=(0, 40))
        
        self.stat_users = self._create_stat_widget("ACTIVE USERS", "0", 3)
        self.stat_rps = self._create_stat_widget("RPS (Req/s)", "0.0", 4)
        self.stat_lat = self._create_stat_widget("LATENCY (ms)", "0", 5)
        self.stat_fail = self._create_stat_widget("FAILURES", "0", 6, color=C_RED)

        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.grid(row=11, column=0, pady=20)
        ctk.CTkLabel(footer, text="Powered by Fanar", font=("Arial", 10), text_color="gray").pack()
        link = ctk.CTkLabel(footer, text="Pouya Rezapour", font=("Arial", 11, "underline"), text_color=C_ACCENT, cursor="hand2")
        link.pack()
        link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/pouyarer"))

    def _create_stat_widget(self, title, value, row, color=C_TEXT):
        f = ctk.CTkFrame(self.sidebar, fg_color="#151515", corner_radius=6)
        f.grid(row=row, column=0, padx=15, pady=8, sticky="ew")
        
        ctk.CTkLabel(f, text=title, font=("Arial", 9, "bold"), text_color="gray", anchor="w").pack(fill="x", padx=10, pady=(8, 0))
        lbl_val = ctk.CTkLabel(f, text=value, font=("Consolas", 24, "bold"), text_color=color, anchor="w")
        lbl_val.pack(fill="x", padx=10, pady=(0, 8))
        return lbl_val

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

    def _switch_tab(self, value):
        if self.running:
            messagebox.showwarning("Locked", "Test running. Stop first.")
            self.nav_btns.set("Load Scenario")
            return
        self.tabs.set(value)

    def _init_terminal(self):
        term_frame = ctk.CTkFrame(self, height=160, fg_color="#000000", corner_radius=0)
        term_frame.grid(row=1, column=1, sticky="ew", padx=0, pady=0)
        
        head = ctk.CTkFrame(term_frame, height=25, fg_color="#222", corner_radius=0)
        head.pack(fill="x")
        ctk.CTkLabel(head, text="SYSTEM TERMINAL", font=("Consolas", 10, "bold"), text_color="gray").pack(side="left", padx=10)
        ctk.CTkButton(head, text="CLEAR", width=50, height=18, fg_color="#333", font=("Arial", 9), 
                      command=lambda: self.console.delete("0.0", "end")).pack(side="right", padx=5, pady=2)

        self.console = ctk.CTkTextbox(term_frame, height=135, font=("Consolas", 11), text_color=C_GREEN, fg_color="transparent")
        self.console.pack(fill="both", expand=True, padx=5, pady=5)
        self.log("StormQA Core Initialized.")

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.console.insert("end", f"[{ts}] > {msg}\n")
        self.console.see("end")

    # ================= LOAD SCENARIO UI =================
    def _build_load_ui(self):
        scroll = ctk.CTkScrollableFrame(self.tab_load, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        card_conf = ctk.CTkFrame(scroll, fg_color="#222")
        card_conf.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(card_conf, text="TARGET URL/IP:", font=("Arial", 12, "bold")).pack(side="left", padx=15, pady=15)
        self.url_entry = ctk.CTkEntry(card_conf, placeholder_text="https://example.com OR 192.168.1.1 ", width=400, border_color="#444")
        self.url_entry.pack(side="left", padx=5)

        card_steps = ctk.CTkFrame(scroll, fg_color="#222")
        card_steps.pack(fill="x", padx=20, pady=10)
        
        h = ctk.CTkFrame(card_steps, fg_color="transparent")
        h.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(h, text="TEST SCENARIO", font=("Arial", 14, "bold"), text_color="white").pack(side="left", pady=5)
        ctk.CTkButton(h, text="+ Add Step", width=80, height=25, fg_color="#444", command=self._add_step).pack(side="right")

        cols = ctk.CTkFrame(card_steps, fg_color="#111", height=30)
        cols.pack(fill="x", padx=10)
        ctk.CTkLabel(cols, text="#", width=30).pack(side="left")
        ctk.CTkLabel(cols, text="Users", width=80).pack(side="left", padx=5)
        ctk.CTkLabel(cols, text="Duration(s)", width=80).pack(side="left", padx=5)
        ctk.CTkLabel(cols, text="Ramp(s)", width=80).pack(side="left", padx=5)
        ctk.CTkLabel(cols, text="Think(s)", width=80).pack(side="left", padx=5)

        self.steps_box = ctk.CTkFrame(card_steps, fg_color="transparent")
        self.steps_box.pack(fill="x", padx=10, pady=5)
        self._add_step() 

        card_act = ctk.CTkFrame(scroll, fg_color="transparent")
        card_act.pack(fill="x", padx=20, pady=10)
        
        self.btn_start = ctk.CTkButton(card_act, text="START STORM ⚡️", height=50, 
                                       font=("Arial", 16, "bold"),
                                       fg_color=C_ACCENT, hover_color="#154c79", command=self.toggle_test)
        self.btn_start.pack(fill="x", pady=5)

        self.btn_pdf = ctk.CTkButton(card_act, text="DOWNLOAD REPORT (PDF)", state="disabled", height=40,
                                     font=("Arial", 12, "bold"),
                                     fg_color=C_GREEN, hover_color="#1e8449", command=self._export_pdf)
        self.btn_pdf.pack(fill="x", pady=5)

        chart_box = ctk.CTkFrame(scroll, height=300, fg_color="#222")
        chart_box.pack(fill="x", padx=20, pady=10)
        self._setup_chart(chart_box)
        
        self.console = ctk.CTkTextbox(scroll, height=150, font=("Consolas", 12), fg_color="#111", text_color="#00ff00")
        self.console.pack(fill="x", padx=20, pady=10)

    def _add_step(self):
        row = ctk.CTkFrame(self.steps_box, fg_color="transparent")
        row.pack(fill="x", pady=2)
        idx = len(self.steps_ui) + 1
        
        lbl = ctk.CTkLabel(row, text=f"{idx}", width=30)
        lbl.pack(side="left")
        
        def entry(v):
            e = ctk.CTkEntry(row, width=80, border_color="#444", justify="center")
            e.insert(0, v)
            e.pack(side="left", padx=5)
            return e

        e_u = entry("10"); e_d = entry("30"); e_r = entry("5"); e_t = entry("0.5")
        
        b_del = ctk.CTkButton(row, text="✖", width=30, height=30, 
                              fg_color="#333", hover_color=C_RED, text_color="white",
                              command=lambda: self._del_step(row))
        b_del.pack(side="right", padx=5)
        
        self.steps_ui.append({"frame": row, "lbl": lbl, "u": e_u, "d": e_d, "r": e_r, "t": e_t})

    def _del_step(self, frame):
        for s in self.steps_ui:
            if s["frame"] == frame:
                self.steps_ui.remove(s)
                break
        frame.destroy()
        for i, s in enumerate(self.steps_ui):
            s["lbl"].configure(text=str(i+1))

    # ================= CHART (MATPLOTLIB) =================
    def _setup_chart(self, parent):
        self.fig = Figure(figsize=(5, 3), dpi=100, facecolor="#222")
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#1a1a1a")
        self.ax.tick_params(colors='gray', labelsize=8)
        self.ax.spines['bottom'].set_color('#444')
        self.ax.spines['left'].set_color('#444')
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.grid(True, color="#333", linestyle='--', linewidth=0.5)
        
        self.line, = self.ax.plot([], [], color=C_ACCENT, linewidth=1.5)
        self.fill = None
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        self.x_data, self.y_data = [0], [0]

    def _update_chart(self, stats):
        self.after(0, lambda: self._draw(stats))

    def _draw(self, stats):
        if stats.get('rps', 0) > 0 and int(stats['rps']) % 5 == 0:
             self.log(f"⚡ {stats['users']} Users | {stats['rps']:.1f} RPS | {stats['avg_latency']:.0f}ms")

        self._update_sidebar_stats(stats['users'], f"{stats['rps']:.1f}", f"{stats['avg_latency']:.0f} ms", stats['failed'])

        self.x_data.append(len(self.x_data))
        self.y_data.append(stats["users"])
        
        if len(self.x_data) > 100:
            self.x_data.pop(0)
            self.y_data.pop(0)

        if len(self.x_data) < 2 or min(self.x_data) == max(self.x_data):
             self.ax.set_xlim(0, 10) 
        else:
             self.ax.set_xlim(min(self.x_data), max(self.x_data))

        ymax = max(self.y_data) if self.y_data else 10
        self.ax.set_ylim(0, max(10, ymax * 1.2))
        
        self.line.set_data(self.x_data, self.y_data)
        
        if self.fill: self.fill.remove()
        self.fill = self.ax.fill_between(self.x_data, 0, self.y_data, color=C_ACCENT, alpha=0.1)
        
        self.canvas.draw_idle() 

    def _update_sidebar_stats(self, u, r, l, f):
        self.stat_users.configure(text=str(u))
        self.stat_rps.configure(text=str(r))
        self.stat_lat.configure(text=str(l))
        self.stat_fail.configure(text=str(f))

    # ================= LOGIC =================
    def toggle_test(self):
        if not self.running:
            raw = self.url_entry.get().strip()
            if not raw: return messagebox.showerror("Error", "URL Required")
            
            # --- FIX: Define url variable correctly ---
            url = f"http://{raw}" if not raw.startswith("http") else raw
            # ------------------------------------------

            steps = []
            try:
                for s in self.steps_ui:
                    steps.append({
                        "users": int(s["u"].get()),
                        "duration": int(s["d"].get()),
                        "ramp": int(s["r"].get()),
                        "think": float(s["t"].get())
                    })
            except: return messagebox.showerror("Error", "Check inputs.")

            self.running = True
            self.btn_start.configure(text="STOP TEST ⏹️", fg_color=C_RED)
            self.btn_pdf.configure(state="disabled")
            
            # Reset Chart & Stats
            self.x_data, self.y_data = [0], [0]
            if self.fill: self.fill.remove(); self.fill = None
            self._update_sidebar_stats(0, 0, 0, 0)
            
            self.log(f"Starting Scenario on {url}...")
            threading.Thread(target=self._run, args=(url, steps), daemon=True).start()
        else:
            self.running = False
            self.engine._stop_event.set()
            self.log("Stopping...")

    def _run(self, url, steps):
        try:
            res = asyncio.run(self.engine.start_scenario(url, steps, self._update_chart))
            self.test_results_cache["Load Test"] = res
            self.after(0, self._finish, res)
        except Exception as e:
            self.log(f"Err: {e}")
            self.running = False
            self.after(0, self._reset_ui)

    def _finish(self, res):
        self._reset_ui()
        self.log(f"Done. Failures: {res['failed_requests']}")
        messagebox.showinfo("Done", "Test Completed.")

    def _reset_ui(self):
        self.running = False
        self.btn_start.configure(text="START LOAD TEST 🚀", fg_color=C_ACCENT)
        self.btn_pdf.configure(state="normal")

    def _export_pdf(self):
        if not self.test_results_cache: return
        path = generate_report(self.test_results_cache)
        if "Error" in path: messagebox.showerror("Error", path)
        else: 
            self.log(f"Report: {path}")
            messagebox.showinfo("Saved", f"PDF Saved:\n{path}")
            
    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.console.insert("end", f"[{ts}] {msg}\n")
        self.console.see("end")

    # ================= SIMPLE TABS =================
    def _build_net_ui(self):
        f = ctk.CTkFrame(self.tab_net, fg_color="transparent")
        f.pack(fill="both", padx=50, pady=50)
        ctk.CTkLabel(f, text="NETWORK SIM", font=("Arial", 20)).pack(pady=20)
        self.n_u = ctk.CTkEntry(f, width=400, placeholder_text="URL"); self.n_u.pack(pady=10)
        self.n_p = ctk.CTkOptionMenu(f, values=list(NETWORK_PROFILES.keys())); self.n_p.pack(pady=10)
        ctk.CTkButton(f, text="RUN", width=200, height=40, command=self._run_net).pack(pady=20)
        self.n_l = ctk.CTkLabel(f, text="Ready"); self.n_l.pack()

    def _run_net(self):
        u = self.n_u.get()
        if not u: return
        if not u.startswith("http"): u = f"http://{u}"
        
        self.log(f"Network Check: {u}")
        res = asyncio.run(run_network_check(u, self.n_p.get()))
        self.test_results_cache["Network"] = res
        
        # --- FIXED HERE ---
        if res.get('status') == 'success':
            delay = res.get('simulated_delay', 0)
            color = C_GREEN if delay < 500 else ("#F1C40F" if delay < 1000 else C_RED)
            msg = f"Connected | Latency: {delay}ms"
        else:
            msg = f"Failed: {res.get('message', 'Error')}"
            color = C_RED
            
        self.n_l.configure(text=msg, text_color=color)
        # ------------------

    def _build_db_ui(self):
        f = ctk.CTkFrame(self.tab_db, fg_color="transparent")
        f.pack(fill="both", padx=20, pady=20)
        self.d_u = ctk.CTkEntry(f, width=400, placeholder_text="DB API"); self.d_u.pack(pady=20)
        ctk.CTkButton(f, text="DISCOVER", command=lambda: self._run_db("discovery")).pack(pady=5)
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