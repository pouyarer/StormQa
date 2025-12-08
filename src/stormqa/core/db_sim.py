import asyncio
import time
import httpx
from typing import Dict, Any, List

COMMON_PATTERNS = {
    "read": [
        "/api/users", "/api/v1/users", "/users",  
        "/api/products", "/api/v1/products", 
        "/api/login", "/login",                   
        "/health", "/api/health",                 
        "/wp-json", "/wp-admin",                  
        "/admin", "/administrator",               
        "/posts", "/comments",
        "/robots.txt", "/sitemap.xml"  
    ],
    "write": ["/api/users", "/api/login", "/users"]
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/json,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

async def _probe(client, base_url, endpoint, method):
    url = f"{base_url.rstrip('/')}{endpoint}"
    try:
        if method == "GET":
            resp = await client.get(url, headers=HEADERS, timeout=5, follow_redirects=True)
        else:
            resp = await client.post(url, json={"test": "stormqa"}, headers=HEADERS, timeout=5, follow_redirects=True)
        
        print(f"   Testing {endpoint:<20} -> Final Status: {resp.status_code}")
        
        
        return resp.status_code
    except Exception as e:
        return 0

async def run_smart_db_test(base_url: str, mode: str = "discovery") -> Dict[str, Any]:
    print(f"\n[DB Sim] Running in mode: {mode} on {base_url}")
    
    if mode == "connection_flood":
        return await _run_connection_flood(base_url)
    
    # Discovery Mode
    found_endpoints = []
    
    async with httpx.AsyncClient(limits=httpx.Limits(max_connections=20), verify=False, follow_redirects=True) as client:
        tasks = []
        for pat in COMMON_PATTERNS["read"]:
            tasks.append(_probe(client, base_url, pat, "GET"))
        
        results = await asyncio.gather(*tasks)
        
        for i, status in enumerate(results):
            if (200 <= status < 300) or status in [401, 403]:
                found_endpoints.append(COMMON_PATTERNS["read"][i])

    print(f"[DB Sim] Found {len(found_endpoints)} valid endpoints.")
    
    return {
        "mode": "discovery",
        "endpoints_found": found_endpoints,
        "count": len(found_endpoints),
        "note": "Redirects followed automatically."
    }

async def _run_connection_flood(base_url: str) -> Dict[str, Any]:
    limit = 50 
    success = 0
    failed = 0
    
    print("[DB Sim] Starting Connection Flood...")
    async with httpx.AsyncClient(limits=httpx.Limits(max_connections=limit), headers=HEADERS, verify=False, follow_redirects=True) as client:
        tasks = []
        target = f"{base_url.rstrip('/')}" 
        
        start = time.monotonic()
        for _ in range(limit * 2): 
            tasks.append(client.get(target, timeout=3))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for r in results:
            if not isinstance(r, Exception) and r.status_code < 500:
                success += 1
            else:
                failed += 1
                
    return {
        "mode": "connection_flood",
        "attempted_connections": len(tasks),
        "held_successfully": success,
        "dropped_or_timeout": failed,
        "duration": time.monotonic() - start
    }