import asyncio
import time
import httpx
from typing import Dict, Any, List

async def fetch(client: httpx.AsyncClient, url: str) -> Dict[str, Any]:
    start_time = time.monotonic()
    try:
        response = await client.get(url, timeout=15)
        response.raise_for_status()
        return {
            "status": "success",
            "duration_ms": (time.monotonic() - start_time) * 1000,
            "http_status": response.status_code,
        }
    except httpx.HTTPStatusError as e:
        return {
            "status": "failed",
            "duration_ms": (time.monotonic() - start_time) * 1000,
            "http_status": e.response.status_code,
        }
    except httpx.RequestError:
        return {
            "status": "error",
            "duration_ms": (time.monotonic() - start_time) * 1000,
            "http_status": None,
        }

async def run_load_test(url: str, requests_count: int, concurrency: int) -> Dict[str, Any]:
    print("\n[Core Engine] Test is running...")
    
    start_total_time = time.monotonic()
    tasks = []
    
    # Added follow_redirects=True
    async with httpx.AsyncClient(
        follow_redirects=True, 
        limits=httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)
    ) as client:
        for _ in range(requests_count):
            tasks.append(fetch(client, url))
        
        results: List[Dict[str, Any]] = await asyncio.gather(*tasks)
    
    total_duration_sec = time.monotonic() - start_total_time
    
    successful_requests = [r for r in results if r["status"] == "success"]
    failed_requests = [r for r in results if r["status"] in ["failed", "error"]]
    response_times = [r["duration_ms"] for r in successful_requests]
    
    summary = {
        "total_duration_sec": total_duration_sec,
        "successful_requests": len(successful_requests),
        "failed_requests": len(failed_requests),
        "min_response_time_ms": min(response_times) if response_times else 0,
        "max_response_time_ms": max(response_times) if response_times else 0,
        "avg_response_time_ms": sum(response_times) / len(response_times) if response_times else 0,
        "throughput_rps": requests_count / total_duration_sec if total_duration_sec > 0 else 0,
        "error_rate_percent": (len(failed_requests) / requests_count) * 100 if requests_count > 0 else 0,
    }
    return summary
