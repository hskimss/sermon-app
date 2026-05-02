# Sermon App v2 (Mac local)

## 설치
```
brew install ffmpeg
cd "/Users/hwasungkim/Library/CloudStorage/GoogleDrive-sharonkim71@gmail.com/내 드라이브/AI/교회 앱/sermon-app"
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 실행
```
python app/server.py
```
http://localhost:5001

## Step 1 수동 검증
```
curl http://localhost:5001/healthz
# {"ok":true}

curl -X POST -H "Content-Type: application/json" \
  -d '{"youtube_url":"https://youtu.be/abc12345678","start_sec":0,"end_sec":2700,"mode":"longform"}' \
  http://localhost:5001/api/job/new
# {"job_id":"...","reused":false,"phase":"queued"}

# 같은 입력 다시 → reused: true
```
