import asyncio
import time
import httpx
from typing import Dict, Any, List

# Common API patterns to simulate database-like transactions
COMMON_PATTERNS = {
    "read": ["/users", "/products", "/posts", "/api/v1/items", "/items/1"],
    "write": ["/users", "/products", "/posts", "/api/v1/items"]  # for POST
}

async def simulate_transaction(client: httpx.AsyncClient, base_url: str, pattern: str, method: str) -> Dict[str, Any]:
    """Simulates a single transaction (HTTP request)."""
    url = f"{base_url.rstrip('/')}{pattern}"
    start_time = time.monotonic()
    try:
        if method == "GET":
            response = await client.get(url, timeout=5)
        elif method == "POST":
            # Send an empty JSON body for simplicity
            response = await client.post(url, json={}, timeout=5)
        
        # We only consider success codes or common errors
        # 404 (Not Found) means the pattern does not exist; we don't count it as error
        if 200 <= response.status_code < 400:
            return {"status": "success", "duration_ms": (time.monotonic() - start_time) * 1000}
        else:
            return {"status": "ignored", "duration_ms": 0}

    except httpx.RequestError:
        return {"status": "error", "duration_ms": (time.monotonic() - start_time) * 1000}


async def run_db_test(base_url: str) -> Dict[str, Any]:
    """Run simulated database test by trying common API patterns."""
    print("\n[DB Sim] Discovering common API endpoints to simulate transactions...")
    tasks = []
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        # Simulate read transactions
        for pattern in COMMON_PATTERNS["read"]:
            tasks.append(simulate_transaction(client, base_url, pattern, "GET"))
            
        # Simulate write transactions
        for pattern in COMMON_PATTERNS["write"]:
            tasks.append(simulate_transaction(client, base_url, pattern, "POST"))
            
        results: List[Dict[str, Any]] = await asyncio.gather(*tasks)

    # Analyze results
    successful_tx = [r for r in results if r["status"] == "success"]
    failed_tx = [r for r in results if r["status"] == "error"]
    response_times = [r["duration_ms"] for r in successful_tx]

    summary = {
        "total_simulated_tx": len(successful_tx) + len(failed_tx),
        "successful_tx": len(successful_tx),
        "failed_tx": len(failed_tx),
        "avg_response_time_ms": sum(response_times) / len(response_times) if response_times else 0,
    }
    return summary
