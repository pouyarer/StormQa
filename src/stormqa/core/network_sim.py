import asyncio
import random
import httpx
from typing import Dict, Any

NETWORK_PROFILES = {
    "GOOD_WIFI": {"latency": 20, "jitter": 5, "loss": 0},
    "4G_LTE": {"latency": 50, "jitter": 15, "loss": 0.5},
    "3G_SLOW": {"latency": 300, "jitter": 100, "loss": 2.0},
    "METRO_SPOT": {"latency": 800, "jitter": 300, "loss": 10.0}, # نوسان شدید
}

async def run_network_check(
    url: str, 
    profile_name: str = "GOOD_WIFI",
    custom_latency: int = 0,
    custom_loss: float = 0
) -> Dict[str, Any]:
    
    if profile_name in NETWORK_PROFILES:
        config = NETWORK_PROFILES[profile_name]
    else:
        config = {"latency": custom_latency, "jitter": 0, "loss": custom_loss}

    print(f"[Network Sim] Applying profile: {profile_name} | {config}")

    if random.random() * 100 < config["loss"]:
        return {
            "status": "packet_loss",
            "latency_simulated": 0,
            "message": "Packet dropped simulated."
        }

    jitter_val = random.randint(-config.get("jitter", 0), config.get("jitter", 0))
    final_latency = max(0, config["latency"] + jitter_val)
    
    await asyncio.sleep(final_latency / 1000.0)

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            start_t = asyncio.get_event_loop().time()
            resp = await client.get(url, timeout=15)
            real_network_time = (asyncio.get_event_loop().time() - start_t) * 1000
            
            return {
                "status": "success",
                "http_code": resp.status_code,
                "simulated_delay": final_latency,
                "real_network_time": real_network_time,
                "total_time": final_latency + real_network_time
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}