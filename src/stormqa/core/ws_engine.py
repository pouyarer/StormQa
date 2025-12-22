import asyncio
import time
import websockets
import json
from typing import Dict, Any

async def run_websocket_test(url: str, message: str = "Ping", duration: int = 5) -> Dict[str, Any]:
    print(f"\n[WS Engine] Connecting to {url}...")
    
    stats = {
        "status": "pending",
        "messages_sent": 0,
        "messages_received": 0,
        "errors": 0,
        "latencies": [],
        "log": []
    }

    try:
        async with websockets.connect(url) as ws:
            stats["log"].append("✅ Connected to Server")
            start_time = time.monotonic()
            
            while time.monotonic() - start_time < duration:
                msg_start = time.monotonic()
                
                try:
                    await ws.send(message)
                    stats["messages_sent"] += 1
                except Exception as e:
                    stats["errors"] += 1
                    stats["log"].append(f"❌ Send Error: {str(e)}")
                    break

                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    stats["messages_received"] += 1
                    
                    latency = (time.monotonic() - msg_start) * 1000
                    stats["latencies"].append(latency)
                    
                    if stats["messages_received"] <= 3:
                        stats["log"].append(f"📩 Recv: {str(response)[:50]}... ({latency:.1f}ms)")
                        
                except asyncio.TimeoutError:
                    stats["errors"] += 1
                    stats["log"].append("⚠️ Timeout waiting for response")
                
                await asyncio.sleep(0.5)

            stats["status"] = "success"
            stats["log"].append("🏁 Test Completed")

    except Exception as e:
        stats["status"] = "failed"
        stats["log"].append(f"🔥 Connection Failed: {str(e)}")

    avg_lat = sum(stats["latencies"]) / len(stats["latencies"]) if stats["latencies"] else 0
    
    return {
        "status": stats["status"],
        "sent": stats["messages_sent"],
        "received": stats["messages_received"],
        "avg_latency": avg_lat,
        "errors": stats["errors"],
        "logs": stats["log"]
    }