import asyncio
import time
import random
import httpx
from typing import Dict, Any, List, Optional, Callable

class LoadTestEngine:
    def __init__(self):
        self._stop_event = asyncio.Event()
        self.stats = {
            "total_requests": 0, "success": 0, "failed": 0,
            "current_users": 0, "response_times": [], "start_time": 0
        }

    async def _user_session(self, client: httpx.AsyncClient, url: str, think_time: float, step_end_time: float,
                            method: str = "GET", headers: dict = None, data: dict = None, assertion: str = None):
        
        while not self._stop_event.is_set() and time.monotonic() < step_end_time:
            request_start = time.monotonic()
            try:
                if method == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method == "PUT":
                    response = await client.put(url, headers=headers, json=data)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    response = await client.get(url, headers=headers)
                
                duration = (time.monotonic() - request_start) * 1000
                self.stats["total_requests"] += 1
                
                is_success = response.status_code < 400
                
                # بررسی Assertion
                if is_success and assertion:
                    if assertion not in response.text:
                        is_success = False 

                if is_success:
                    self.stats["success"] += 1
                    self.stats["response_times"].append(duration)
                else:
                    self.stats["failed"] += 1

            except Exception as e:
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
        assertion: Optional[str] = None
    ) -> Dict[str, Any]:
        
        if not url.startswith("http"): url = f"http://{url}"
        print(f"\n[Engine] Starting {method} on {url} (VPN Bypass Enabled)")
        
        self._stop_event.clear()
        self.stats = {"total_requests": 0, "success": 0, "failed": 0, "current_users": 0, "response_times": [], "start_time": time.monotonic()}
        
        max_users = max(int(s['users']) for s in steps)
        limits = httpx.Limits(max_connections=max_users + 50, max_keepalive_connections=max_users + 50)

        async with httpx.AsyncClient(
            limits=limits, 
            timeout=10.0, 
            follow_redirects=True, 
            verify=False, 
            trust_env=False 
        ) as client:
            
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
                    
                    if current_time < ramp_time:
                        needed = int((current_time / ramp_time) * target_users)
                    else:
                        needed = target_users
                    
                    current = self.stats["current_users"]
                    if current < needed:
                        for _ in range(needed - current):
                            asyncio.create_task(self._user_session(client, url, think_val, step_end, method, headers, body, assertion))
                            self.stats["current_users"] += 1
                    
                    if stats_callback:
                        elapsed = time.monotonic() - self.stats["start_time"]
                        avg_lat = sum(self.stats["response_times"][-50:]) / len(self.stats["response_times"][-50:]) if self.stats["response_times"] else 0
                        stats_callback({
                            "users": self.stats["current_users"],
                            "rps": self.stats["total_requests"] / elapsed if elapsed > 0 else 0,
                            "avg_latency": avg_lat,
                            "failed": self.stats["failed"],
                            "step": i + 1
                        })
                    await asyncio.sleep(0.1)
                
                self.stats["current_users"] = 0 
                await asyncio.sleep(0.5)

            self._stop_event.set()

        total_time = time.monotonic() - self.stats["start_time"]
        avg_resp = sum(self.stats["response_times"]) / len(self.stats["response_times"]) if self.stats["response_times"] else 0
        return {
            "total_duration_sec": total_time,
            "total_requests": self.stats["total_requests"],
            "successful_requests": self.stats["success"],
            "failed_requests": self.stats["failed"],
            "avg_response_time_ms": avg_resp,
            "throughput_rps": self.stats["success"] / total_time if total_time > 0 else 0,
        }