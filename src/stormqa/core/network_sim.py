import asyncio
import random
import httpx
from typing import Dict, Any

async def run_network_test(
    url: str, 
    latency_ms: int, 
    packet_loss_percent: float
) -> Dict[str, Any]:
    summary = {
        "latency_applied_ms": latency_ms,
        "packet_loss_applied_percent": packet_loss_percent,
        "request_successful": False
    }

    if random.random() * 100 < packet_loss_percent:
        print("[Network Sim] Packet lost!")
        return summary

    print(f"[Network Sim] Applying {latency_ms}ms latency...")
    await asyncio.sleep(latency_ms / 1000.0)

    try:
        # Added follow_redirects=True
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, timeout=15)
            response.raise_for_status()
            summary["request_successful"] = True
            print("[Network Sim] Request successful.")
    except httpx.RequestError as e:
        print(f"[Network Sim] Request failed after applying conditions: {e}")

    return summary
