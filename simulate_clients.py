import asyncio
import aiohttp
import time
import json
import sys

TARGET_URL = "http://127.0.0.1:8090/ingest"
CLIENT_COUNT = int(sys.argv[1]) if len(sys.argv) > 1 else 200
MIX_PRIO = 0.20  # 20% priority traffic

async def fire_one(session, is_prio):
    start = time.perf_counter()
    headers = {"X-Priority-Traffic": "true"} if is_prio else {}
    try:
        async with session.post(TARGET_URL, json={"prio": is_prio}, headers=headers) as resp:
            await resp.read()  # Fully consume runtime body
            status = resp.status
            shed_reason = resp.headers.get("X-Shed-Reason", None) if status == 503 else None
    except Exception:
        status = "Network Error"
        shed_reason = None
        
    latency_ms = (time.perf_counter() - start) * 1000
    return status, latency_ms, shed_reason

async def run_batch():
    # Structural limit config setup
    timeout_config = aiohttp.ClientTimeout(total=1.5)
    async with aiohttp.ClientSession(timeout=timeout_config) as session:
        tasks = []
        for i in range(CLIENT_COUNT):
            is_prio = (i % int(1/MIX_PRIO) == 0) if MIX_PRIO > 0 else False
            tasks.append(fire_one(session, is_prio))
        results = await asyncio.gather(*tasks, return_exceptions=False)

    status_counts = {}
    shed_reasons = {}
    latencies = []
    
    for status, lat, reason in results:
        status_counts[status] = status_counts.get(status, 0) + 1
        latencies.append(lat)
        if reason:
            shed_reasons[reason] = shed_reasons.get(reason, 0) + 1

    avg = sum(latencies) / len(latencies)
    sorted_lats = sorted(latencies)
    p95 = sorted_lats[int(0.95 * len(sorted_lats)) - 1]
    p99 = sorted_lats[int(0.99 * len(sorted_lats)) - 1]

    print("\n⏱️  === LATENCY PROFILE ===")
    print(f"  ↳ Avg Latency:       {avg:.2f} ms")
    print(f"  ↳ 95th Percentile:   {p95:.2f} ms")
    print(f"  ↳ 99th Percentile:   {p99:.2f} ms")
    print(f"📊 Status Summary:     {json.dumps(status_counts)}")
    if shed_reasons:
        print(f"🚫 Shedding Reasons:   {json.dumps(shed_reasons)}")

if __name__ == "__main__":
    asyncio.run(run_batch())
