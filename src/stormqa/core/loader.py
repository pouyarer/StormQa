import asyncio
import time
import random
import httpx
from typing import Dict, Any, List, Optional, Callable

class LoadTestEngine:
    def __init__(self):
        self._stop_event = asyncio.Event()
        self.stats = {
            "total_requests": 0,
            "success": 0,
            "failed": 0,
            "current_users": 0,
            "response_times": [],
            "start_time": 0
        }

    async def _user_session(self, client: httpx.AsyncClient, url: str, think_time: float, step_end_time: float):

        while not self._stop_event.is_set() and time.monotonic() < step_end_time:
            request_start = time.monotonic()
            try:
                response = await client.get(url)
                duration = (time.monotonic() - request_start) * 1000
                
                self.stats["total_requests"] += 1
                if response.status_code < 400:
                    self.stats["success"] += 1
                    self.stats["response_times"].append(duration)
                else:
                    self.stats["failed"] += 1

            except Exception:
                self.stats["failed"] += 1
            
            if think_time > 0:

                jitter = think_time * 0.2
                actual_delay = random.uniform(max(0, think_time - jitter), think_time + jitter)
                await asyncio.sleep(actual_delay)
            else:
                await asyncio.sleep(0.01)

    async def start_scenario(
        self,
        url: str,
        steps: List[Dict], 
        stats_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        
        if not url.startswith("http"):
            url = f"http://{url}"

        print(f"\n[Engine] Starting Scenario on {url} | Steps: {len(steps)}")
        
        self._stop_event.clear()
        self.stats = {"total_requests": 0, "success": 0, "failed": 0, "current_users": 0, "response_times": [], "start_time": time.monotonic()}
        
        max_users_ever = max(int(s['users']) for s in steps)
        limits = httpx.Limits(max_connections=max_users_ever + 50, max_keepalive_connections=max_users_ever + 50)

        async with httpx.AsyncClient(limits=limits, timeout=10.0, follow_redirects=True) as client:
            
            for i, step in enumerate(steps):
                if self._stop_event.is_set(): break
                
                target_users = int(step['users'])
                duration = int(step['duration'])
                ramp_time = int(step['ramp'])
                think_val = float(step.get('think', 0))
                
                print(f"--- Running Step {i+1}: Target {target_users} Users, Think: {think_val}s ---")
                
                step_start_time = time.monotonic()
                step_end_time = step_start_time + duration
                active_tasks = []
                
                while time.monotonic() < step_end_time and not self._stop_event.is_set():
                    current_step_time = time.monotonic() - step_start_time
                    
                    if current_step_time < ramp_time:
                        users_needed_now = int((current_step_time / ramp_time) * target_users)
                    else:
                        users_needed_now = target_users
                    
                    current_active = self.stats["current_users"]
                    if current_active < users_needed_now:
                        needed = users_needed_now - current_active
                        for _ in range(needed):

                            task = asyncio.create_task(
                                self._user_session(client, url, think_val, step_end_time)
                            )
                            active_tasks.append(task)
                            self.stats["current_users"] += 1
                    

                    if stats_callback:
                        elapsed = time.monotonic() - self.stats["start_time"]
                        recent_avg = 0
                        if self.stats["response_times"]:
                            recent = self.stats["response_times"][-50:]
                            recent_avg = sum(recent) / len(recent)
                        
                        stats_callback({
                            "users": self.stats["current_users"],
                            "rps": self.stats["total_requests"] / elapsed if elapsed > 0 else 0,
                            "avg_latency": recent_avg,
                            "failed": self.stats["failed"],
                            "step": i + 1
                        })
                    
                    await asyncio.sleep(0.1)
                

                self.stats["current_users"] = 0 
                await asyncio.sleep(0.5)

            self._stop_event.set()


        total_time = time.monotonic() - self.stats["start_time"]
        

        avg_resp = 0
        if self.stats["response_times"]:
            avg_resp = sum(self.stats["response_times"]) / len(self.stats["response_times"])

        return {
            "total_duration_sec": total_time,
            "total_requests": self.stats["total_requests"],
            "successful_requests": self.stats["success"],
            "failed_requests": self.stats["failed"],
            "avg_response_time_ms": avg_resp,
            "throughput_rps": self.stats["success"] / total_time if total_time > 0 else 0,
        }