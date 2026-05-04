import sys, json, time, requests, os
sys.path.insert(0, "/tmp/sermon-app")
from app.render.payload import build_short_payload_v4
from pathlib import Path

p = build_short_payload_v4(
    job_id="v4_test",
    clip={"start_sec":0.0,"end_sec":60.0,"id":"v4_test"},
    jobs_dir=Path("/tmp/sermon-app/jobs"),
    austerity_phrase="주님 앞에 잠잠하라",
)
p["audio_url"] = "http://100.116.4.84:9876/v4_audio.mp3"

print("PAYLOAD audio_url:", p.get("audio_url"))
print("PAYLOAD keys:", list(p.keys()))

r = requests.post("http://100.104.121.7:8770/render", json=p, timeout=30)
print("submit status:", r.status_code)
sub = r.json()
print("submit body:", json.dumps(sub)[:500])
rid = sub["render_id"]
print("render_id:", rid)

last = None
for i in range(80):
    time.sleep(3)
    s = requests.get(f"http://100.104.121.7:8770/render/{rid}/status").json()
    st = s.get("status")
    if st != last:
        print(f"[{i*3}s] status={st} warn={s.get('audio_mux_warning','')}")
        last = st
    if st in ("ready", "completed", "failed"):
        print("FINAL:", json.dumps(s)[:500])
        break

with requests.get(f"http://100.104.121.7:8770/output/{rid}.mp4", stream=True) as resp:
    resp.raise_for_status()
    with open("/tmp/sermon-app/renders/v4_with_audio.mp4", "wb") as f:
        for c in resp.iter_content(1<<16):
            f.write(c)

print("DONE:", os.path.getsize("/tmp/sermon-app/renders/v4_with_audio.mp4"))
