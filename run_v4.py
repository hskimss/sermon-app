#!/usr/bin/env python3
"""v4 직접 render 호출 — placeholder 치환 흐름 검증."""
from pathlib import Path
import sys, json, time
sys.path.insert(0, "/tmp/sermon-app")

from app.render.payload import build_short_payload_v4
import requests

JOB = "v4_test"
JOBS_DIR = Path("/tmp/sermon-app/jobs")
HF = "http://100.104.121.7:8770"

clip = {"start_sec": 0.0, "end_sec": 60.0, "id": JOB}
payload = build_short_payload_v4(
    job_id=JOB,
    clip=clip,
    jobs_dir=JOBS_DIR,
    sermon_app_base="http://100.116.4.84:9876",
    austerity_phrase="주님 앞에 잠잠하라",
)

print("=== payload keys ===")
print(list(payload.keys()))
print("=== composition ===", payload.get("composition"))
print("=== scripture_ref ===", payload.get("scripture_ref"))
print("=== scripture_text ===", str(payload.get("scripture_text"))[:80])

# 저장
with open("/tmp/v4_payload.json", "w") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

# 제출
print("\n=== submit to", HF, "===")
r = requests.post(f"{HF}/render", json=payload, timeout=30)
print("status:", r.status_code)
print("body:", r.text[:300])
sub = r.json() if r.ok else None
if not sub:
    sys.exit(1)

rid = sub["render_id"]
print("\n=== render_id:", rid, "===")

# poll
for i in range(60):
    time.sleep(3)
    s = requests.get(f"{HF}/render/{rid}/status", timeout=10).json()
    print(f"[{i*3}s]", s.get("status"), s.get("message", ""))
    if s.get("status") in ("completed", "failed"):
        break

if s.get("status") != "completed":
    print("FAIL")
    sys.exit(2)

# fetch
print("\n=== fetch mp4 ===")
url = f"{HF}/output/{rid}.mp4"
out = "/tmp/sermon-app/renders/v4_proper.mp4"
with requests.get(url, stream=True, timeout=120) as resp:
    resp.raise_for_status()
    with open(out, "wb") as f:
        for chunk in resp.iter_content(1<<16):
            f.write(chunk)
import os
print("OK:", out, os.path.getsize(out), "bytes")
