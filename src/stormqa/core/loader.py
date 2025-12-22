import asyncio
import time
import random
import httpx
import json
import re
import csv
from typing import Dict, Any, List, Optional, Callable

class LoadTestEngine:
    def __init__(self):
        self._stop_event = asyncio.Event()
        self.stats = {
            "total_requests": 0, "success": 0, "failed": 0,
            "current_users": 0, "response_times": [], "start_time": 0
        }
        self.data_rows = []
        self.scenario_vars = {} 

    def _calculate_percentiles(self, response_times):
        if not response_times:
            return {"p50": 0, "p95": 0, "p99": 0}
        sorted_times = sorted(response_times)
        n = len(sorted_times)
        return {
            "p50": sorted_times[int(n * 0.50)],
            "p95": sorted_times[int(n * 0.95)],
            "p99": sorted_times[int(n * 0.99)]
        }
    
    def _get_dynamic_percentile(self, response_times, p_val: float):
        if not response_times: return 0
        sorted_times = sorted(response_times)
        idx = int(len(sorted_times) * (p_val / 100.0))
        idx = min(idx, len(sorted_times) - 1)
        return sorted_times[idx]

    def _load_data_file(self, file_path: str):
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                self.data_rows = list(reader)
            print(f"[Engine] Loaded {len(self.data_rows)} rows from CSV.")
        except Exception as e:
            print(f"[Engine] Error loading CSV: {e}")
            self.data_rows = []

    def _inject_variables(self, target: Any, row_data: Dict[str, str]) -> Any:
        context = {**self.scenario_vars, **row_data}
        if not context: return target
        if isinstance(target, dict):
            return {k: self._inject_variables(v, context) for k, v in target.items()}
        if isinstance(target, str):
            for key, value in context.items():
                if value is None: continue
                placeholder = "{{" + key + "}}"
                if placeholder in target:
                    target = target.replace(placeholder, str(value))
            return target
        return target

    def _extract_from_response(self, response_text: str, extract_rules: str):
        if not extract_rules: return
        try:
            if "=" in extract_rules:
                var_name, path = extract_rules.split("=", 1)
                var_name, path = var_name.strip(), path.strip()
                extracted_value = None

                if path.startswith("json."):
                    json_key = path.replace("json.", "")
                    try:
                        data = json.loads(response_text)
                        keys = json_key.split('.')
                        val = data
                        for k in keys:
                            if isinstance(val, dict): val = val.get(k)
                            else: val = None; break
                        extracted_value = val
                    except: pass
                elif path.startswith("regex:"):
                    pattern = path.replace("regex:", "")
                    match = re.search(pattern, response_text)
                    if match: extracted_value = match.group(1) if match.groups() else match.group(0)

                if extracted_value:
                    self.scenario_vars[var_name] = str(extracted_value)
        except Exception as e:
            pass
            # print(f"[Engine] Extraction Error: {e}")

    def _evaluate_thresholds(self, metrics: dict, thresholds_str: str, raw_times: list) -> dict:
        if not thresholds_str:
            return {"status": "passed", "failures": []}
        
        failures = []
        rules = [r.strip() for r in thresholds_str.split(',')]
        
        for rule in rules:
            try:
                if '<' in rule: metric_key, limit, operator = *rule.split('<'), 'lt'
                elif '>' in rule: metric_key, limit, operator = *rule.split('>'), 'gt'
                else: continue
                
                metric_key = metric_key.strip().lower()
                limit = float(limit.replace('%', '').strip())
                
                actual_value = 0
                if metric_key.startswith('p'):
                    try:
                        p_val = float(metric_key[1:])
                        actual_value = self._get_dynamic_percentile(raw_times, p_val)
                    except ValueError: actual_value = 0
                elif metric_key == 'avg': actual_value = metrics['avg_response_time_ms']
                elif metric_key == 'error': 
                    total = metrics['total_requests']
                    actual_value = (metrics['failed_requests'] / total * 100) if total > 0 else 0
                
                failed = False
                if operator == 'lt' and actual_value > limit: failed = True
                if operator == 'gt' and actual_value < limit: failed = True
                
                if failed:
                    failures.append(f"{metric_key} ({actual_value:.1f}) failed limit {operator} {limit}")
            except Exception as e:
                pass

        return {"status": "failed" if failures else "passed", "failures": failures}

    async def _user_session(self, client: httpx.AsyncClient, url: str, think_time: float, step_end_time: float,
                            method: str = "GET", headers: dict = None, data: dict = None, assertion: str = None, 
                            extract: str = None, chaos_config: dict = None):
        
        data_index = random.randint(0, len(self.data_rows) - 1) if self.data_rows else 0

        while not self._stop_event.is_set() and time.monotonic() < step_end_time:
            
            # --- CHAOS INJECTION ---
            if chaos_config and chaos_config.get('enabled'):
                if random.randint(0, 100) < int(chaos_config.get('rate', 0)):
                    c_type = chaos_config.get('type', 'latency')
                    if c_type == 'latency':
                        await asyncio.sleep(random.uniform(0.5, 2.0))
                    elif c_type == 'exception':
                        self.stats["total_requests"] += 1 # Count dropped request
                        self.stats["failed"] += 1
                        await asyncio.sleep(0.1)
                        continue 
            # -----------------------

            request_start = time.monotonic()
            
            current_row = {}
            if self.data_rows:
                current_row = self.data_rows[data_index % len(self.data_rows)]
                data_index += 1
            
            final_url = self._inject_variables(url, current_row)
            final_headers = self._inject_variables(headers, current_row) if headers else {}
            
            final_data = data
            if data:
                try:
                    data_str = json.dumps(data)
                    injected_str = self._inject_variables(data_str, current_row)
                    final_data = json.loads(injected_str)
                except: final_data = data

            try:
                if method == "POST": response = await client.post(final_url, headers=final_headers, json=final_data)
                elif method == "PUT": response = await client.put(final_url, headers=final_headers, json=final_data)
                elif method == "DELETE": response = await client.delete(final_url, headers=final_headers)
                else: response = await client.get(final_url, headers=final_headers)
                
                duration = (time.monotonic() - request_start) * 1000
                self.stats["total_requests"] += 1 # ✅ FIX: Count Total
                
                if extract and response.status_code < 400:
                    self._extract_from_response(response.text, extract)

                is_success = response.status_code < 400
                if assertion:
                    if assertion.startswith("status:"):
                        expected_code = int(assertion.split(":")[1])
                        if response.status_code != expected_code: is_success = False
                    elif assertion not in response.text:
                        is_success = False

                if is_success:
                    self.stats["success"] += 1
                    if len(self.stats["response_times"]) < 100000:
                         self.stats["response_times"].append(duration)
                else:
                    self.stats["failed"] += 1

            except Exception as e:
                self.stats["total_requests"] += 1 # ✅ FIX: Count Total even on error
                self.stats["failed"] += 1
            
            if think_time > 0:
                jitter = think_time * 0.2
                delay = random.uniform(max(0, think_time - jitter), think_time + jitter)
                await asyncio.sleep(delay)
            else:
                await asyncio.sleep(0.01)

    async def start_scenario(
        self,
        url: str,
        steps: List[Dict],
        stats_callback: Optional[Callable] = None,
        method: str = "GET",
        headers: Optional[Dict] = None,
        body: Optional[Dict] = None,
        assertion: Optional[str] = None,
        data_file: Optional[str] = None,
        extract: Optional[str] = None,
        thresholds: Optional[str] = None,
        chaos_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        
        self.data_rows = []
        if data_file: self._load_data_file(data_file)
        self.scenario_vars = {}

        if not url.startswith("http"): url = f"http://{url}"
        print(f"\n[Engine] Starting {method} on {url} | Chaos: {chaos_config}")
        
        self._stop_event.clear()
        self.stats = {"total_requests": 0, "success": 0, "failed": 0, "current_users": 0, "response_times": [], "start_time": time.monotonic()}
        
        max_users = max(int(s['users']) for s in steps)
        limits = httpx.Limits(max_connections=max_users + 100, max_keepalive_connections=max_users + 100)
        timeout_config = httpx.Timeout(20.0, connect=10.0)

        # ✅ FIX 1: لیست نگهدارنده تسک‌ها
        active_tasks = []

        async with httpx.AsyncClient(limits=limits, timeout=timeout_config, follow_redirects=True, verify=False, trust_env=False) as client:
            for i, step in enumerate(steps):
                if self._stop_event.is_set(): break
                target_users = int(step['users'])
                duration = int(step['duration'])
                ramp_time = int(step['ramp'])
                think_val = float(step.get('think', 0))
                
                step_start = time.monotonic()
                step_end = step_start + duration
                
                while time.monotonic() < step_end and not self._stop_event.is_set():
                    current_time = time.monotonic() - step_start
                    needed = int((current_time / ramp_time) * target_users) if current_time < ramp_time else target_users
                    current = self.stats["current_users"]
                    
                    if current < needed:
                        for _ in range(needed - current):
                            # ✅ FIX 2: اضافه کردن تسک به لیست
                            task = asyncio.create_task(self._user_session(client, url, think_val, step_end, method, headers, body, assertion, extract, chaos_config))
                            active_tasks.append(task)
                            self.stats["current_users"] += 1
                    
                    if stats_callback:
                        elapsed = time.monotonic() - self.stats["start_time"]
                        recent = self.stats["response_times"][-100:]
                        avg_lat = sum(recent) / len(recent) if recent else 0
                        stats_callback({
                            "users": self.stats["current_users"],
                            "rps": self.stats["total_requests"] / elapsed if elapsed > 0 else 0,
                            "avg_latency": avg_lat,
                            "failed": self.stats["failed"],
                            "step": i + 1
                        })
                    await asyncio.sleep(0.25)
                self.stats["current_users"] = 0 
                await asyncio.sleep(0.5)

            self._stop_event.set()
            
            # ✅ FIX 3: صبر برای اتمام تمام درخواست‌ها
            if active_tasks:
                await asyncio.gather(*active_tasks)

        total_time = time.monotonic() - self.stats["start_time"]
        avg_resp = sum(self.stats["response_times"]) / len(self.stats["response_times"]) if self.stats["response_times"] else 0
        percentiles = self._calculate_percentiles(self.stats["response_times"])

        metrics = {
            "url": url,  # ✅ FIX 4: پاس دادن URL
            "total_duration_sec": total_time,
            "total_requests": self.stats["total_requests"],
            "successful_requests": self.stats["success"],
            "failed_requests": self.stats["failed"],
            "avg_response_time_ms": avg_resp,
            "p50_latency": percentiles['p50'],
            "p95_latency": percentiles['p95'],
            "p99_latency": percentiles['p99'],
            "throughput_rps": self.stats["success"] / total_time if total_time > 0 else 0,
        }

        threshold_result = self._evaluate_thresholds(metrics, thresholds, self.stats["response_times"])
        metrics["test_result"] = threshold_result 

        return metrics