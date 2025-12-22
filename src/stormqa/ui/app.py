import webview
import os
import sys
import threading
import asyncio
import json
import shlex
import time
import webbrowser 
from pathlib import Path

try:
    from stormqa.core.loader import LoadTestEngine
    from stormqa.core.network_sim import run_network_check, NETWORK_PROFILES
    from stormqa.core.db_sim import run_smart_db_test
    from stormqa.core.ws_engine import run_websocket_test
    from stormqa.core.history_manager import init_db, save_test_result, get_recent_history, clear_history
    from stormqa.reporters.main_reporter import generate_report
except ImportError:
    pass

# --- Helper function to save cache for CLI compatibility ---
def write_to_json_cache(data):
    cache_file = Path(".stormqa_cache.json")
    try:
        cache = {}
        if cache_file.exists():
            with open(cache_file, "r") as f:
                cache = json.load(f)
        
        cache["loadTest"] = data
        cache["last_run_type"] = "load"
        
        with open(cache_file, "w") as f:
            json.dump(cache, f, indent=4)
    except Exception as e:
        print(f"Failed to write cache: {e}")

class CurlParser:
    @staticmethod
    def parse(curl_command):
        clean_cmd = curl_command.replace('curl ', '', 1).strip()
        try:
            tokens = shlex.split(clean_cmd)
        except Exception:
            return None, "Parse Error"
        
        parsed = {"method": "GET", "url": "", "headers": {}, "body": None}
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.startswith('http'): parsed["url"] = token; i+=1
            elif token in ('-X', '--request'): parsed["method"] = tokens[i+1].upper(); i+=2
            elif token in ('-H', '--header'):
                if ':' in tokens[i+1]: k,v = tokens[i+1].split(':',1); parsed["headers"][k.strip()]=v.strip()
                i+=2
            elif token in ('-d', '--data'): parsed["body"] = tokens[i+1]; parsed["method"]="POST"; i+=2
            else: i+=1
        return parsed, None

class StormApi:
    def __init__(self):
        self._window = None
        self.engine = LoadTestEngine()
        self.global_stats = {
            "total_tests": 0,
            "total_requests_sent": 0,
            "total_failures": 0,
            "last_test_date": "N/A"
        }
        self.test_results_cache = {}
        
        try:
            init_db()
        except: pass

    def set_window(self, window):
        self._window = window

    def open_link(self, url):
        webbrowser.open(url)

    def select_data_file(self):
        try:
            filename = self._window.create_file_dialog(webview.OPEN_DIALOG, file_types=('CSV Files (*.csv)', 'All files (*.*)'))
            if filename:
                if isinstance(filename, tuple) or isinstance(filename, list): filename = filename[0]
                return filename
        except Exception as e:
            print(e)
        return ""

    def get_global_stats(self): return self.global_stats

    def get_history_chart_data(self):
        return get_recent_history()

    def reset_global_stats(self):
        self.global_stats = {"total_tests": 0, "total_requests_sent": 0, "total_failures": 0, "last_test_date": "N/A"}
        self.test_results_cache = {}
        
        try:
            clear_history()
        except: pass
        
        return {"status": "success", "data": self.global_stats}

    def parse_curl_command(self, curl_cmd):
        data, err = CurlParser.parse(curl_cmd)
        return {"status": "error", "message": err} if err else {"status": "success", "data": data}

    def start_load_test(self, config):
        threading.Thread(target=self._run_engine_thread, args=(config,)).start()
        return {"status": "started"}

    def stop_load_test(self):
        if self.engine: self.engine._stop_event.set()
        return {"status": "stopped"}

    def _run_engine_thread(self, config):
        def stats_callback(stats):
            if self._window: self._window.evaluate_js(f"window.updateLiveStats({json.dumps(stats)})")

        try:
            summary = asyncio.run(self.engine.start_scenario(
                config.get("url"), 
                config.get("steps", []), 
                stats_callback,
                config.get("method"), 
                config.get("headers"), 
                config.get("body"), 
                config.get("assertion"),
                config.get("data_file"),
                config.get("extract"),
                config.get("thresholds"),
                config.get("chaos")
            ))
            
            summary["url"] = config.get("url")

            self.global_stats["total_tests"] += 1
            self.global_stats["total_requests_sent"] += summary["total_requests"]
            self.global_stats["total_failures"] += summary["failed_requests"]
            self.global_stats["last_test_date"] = time.strftime("%Y-%m-%d %H:%M")
            
            # ذخیره در حافظه رم برای دسترسی سریع دکمه اکسپورت
            self.test_results_cache["Load Test"] = summary
            
            # ذخیره در دیتابیس تاریخچه
            save_test_result(summary)
            
            # ✅ FIX 1: ذخیره در فایل جیسون تا اگر کاربر رفت تو ترمینال، اونجا هم ببینه
            write_to_json_cache(summary)

            if self._window: self._window.evaluate_js(f"window.testFinished({json.dumps(summary)})")
        except Exception as e:
            if self._window: self._window.evaluate_js(f"window.testError('{str(e)}')")

    def save_scenario_file(self, data_json):
        try:
            filename = self._window.create_file_dialog(webview.SAVE_DIALOG, directory='', save_filename='scenario.sqa')
            if filename:
                if isinstance(filename, tuple) or isinstance(filename, list): filename = filename[0]
                with open(filename, 'w') as f: f.write(data_json)
                return {"status": "success", "path": filename}
        except Exception as e: print(e)
        return {"status": "cancel"}

    def load_scenario_file(self):
        try:
            filename = self._window.create_file_dialog(webview.OPEN_DIALOG, file_types=('StormQA Files (*.sqa)',))
            if filename:
                if isinstance(filename, tuple) or isinstance(filename, list): filename = filename[0]
                with open(filename, 'r') as f: content = f.read()
                safe_content = json.dumps(json.loads(content))
                if self._window: self._window.evaluate_js(f"window.loadImportedData({safe_content})")
                return {"status": "success"}
        except Exception as e: print(e)
        return {"status": "cancel"}

    def get_network_profiles(self): return list(NETWORK_PROFILES.keys())
    def run_network_test(self, u, p): return asyncio.run(run_network_check(u, p))
    def run_db_test(self, u, m): return asyncio.run(run_smart_db_test(u, m))
    def run_ws_test(self, u, m): return asyncio.run(run_websocket_test(u, m, 5))
    
    def get_ai_analysis(self): 
        if not self.test_results_cache: return "No data."
        lt = self.test_results_cache.get("Load Test")
        if lt:
            err = (lt['failed_requests']/lt['total_requests'])*100 if lt['total_requests'] else 0
            return f"Load Test Analysis:\nError Rate: {err:.1f}%\nAvg Latency: {lt['avg_response_time_ms']:.1f}ms"
        return "No Load Test data found."

    def export_report_pdf(self): 
        try:
            # ✅ FIX 2: فقط دیتای مربوط به Load Test رو می‌فرستیم، نه کل دیکشنری رو
            data_to_report = self.test_results_cache.get("Load Test")
            
            if not data_to_report:
                 return {"status": "error", "message": "No test data available to export."}

            path = generate_report(data_to_report)
            return {"status": "success", "path": path}
        except Exception as e: 
            return {"status": "error", "message": str(e)}

def start_gui():
    api = StormApi()
    base = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    
    icon_path = os.path.join(base, 'assets', 'icon.png')
    if not os.path.exists(icon_path): icon_path = None

    window = webview.create_window(
        'StormQA v3', 
        url=os.path.join(base, 'dist', 'index.html'), 
        js_api=api, 
        width=1280, height=850, 
        background_color='#0f172a'
    )
    api.set_window(window)
    webview.start(debug=False, icon=icon_path)