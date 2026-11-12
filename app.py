import os, json, uuid, subprocess, base64, re
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).parent.resolve()
DATA = Path(os.getenv("DATA_DIR", str(BASE / "data")))
UPLOADS, JOBS, CLIPS = DATA / "uploads", DATA / "jobs", DATA / "clips"
for p in (UPLOADS, JOBS, CLIPS):
    p.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AI Food Video Clip Finder Mobile")
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")
MAX_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024**3)))
FRAME_INTERVAL = max(1, int(os.getenv("FRAME_INTERVAL_SECONDS", "4")))
MAX_FRAMES = max(10, int(os.getenv("MAX_ANALYSIS_FRAMES", "180")))

def run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr[-2500:] or "Command failed")
    return p.stdout

def duration_of(path):
    return float(run(["ffprobe","-v","error","-show_entries","format=duration",
                      "-of","default=noprint_wrappers=1:nokey=1",str(path)]).strip())

def extract_frames(video, folder, duration):
    folder.mkdir(parents=True, exist_ok=True)
    interval = max(FRAME_INTERVAL, int(duration / MAX_FRAMES) + 1)
    frames = []
    for t in range(0, max(1, int(duration)), interval):
        if len(frames) >= MAX_FRAMES: break
        out = folder / f"frame_{t:06d}.jpg"
        subprocess.run(["ffmpeg","-y","-ss",str(t),"-i",str(video),"-frames:v","1",
                        "-vf","scale='min(640,iw)':-2","-q:v","6",str(out)],
                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        if out.exists() and out.stat().st_size: frames.append((t,out))
    return frames

def analyze_with_openai(frames, api_key, duration):
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    content = [{"type":"text","text":
      "Review timestamped sampled frames from a food-vlog video. Identify visually engaging "
      "segments: close-up dishes, cooking/serving, first bite, tasting/reaction, restaurant "
      "ambience, unusual foods. Do not guess dialogue or spoken language. Return ONLY JSON: "
      "{\"highlights\":[{\"start\":0,\"end\":12,\"title\":\"Short Bengali title\","
      "\"reason\":\"Why this scene is visually interesting, in Bengali\",\"score\":8}]}. "
      f"Video duration is {duration:.1f} seconds. Use seconds, keep clips 5-25 seconds, "
      "within duration. Scores 1-10. Avoid duplicate/overlapping picks. Use Bengali for titles "
      "and reasons when possible."}]
    for t, path in frames:
        b64 = base64.b64encode(path.read_bytes()).decode()
        content += [{"type":"text","text":f"Frame timestamp: {t} seconds"},
                    {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}","detail":"low"}}]
    r = client.chat.completions.create(
      model=os.getenv("OPENAI_VISION_MODEL","gpt-4o-mini"),
      messages=[{"role":"user","content":content}], temperature=0.2)
    raw = re.sub(r"^```(?:json)?|```$", "", (r.choices[0].message.content or "").strip(), flags=re.M).strip()
    return json.loads(raw).get("highlights", [])

def process_job(job_id, video_path, api_key):
    jf = JOBS / f"{job_id}.json"
    try:
        duration = duration_of(video_path)
        jf.write_text(json.dumps({"status":"processing","progress":"ভিডিও থেকে দৃশ্য নেওয়া হচ্ছে…"},ensure_ascii=False))
        frames = extract_frames(video_path, DATA/"frames"/job_id, duration)
        jf.write_text(json.dumps({"status":"processing","progress":f"{len(frames)}টি দৃশ্য AI বিশ্লেষণ করছে…"},ensure_ascii=False))
        raw = analyze_with_openai(frames, api_key, duration)
        highlights = []
        for h in raw:
            try:
                a = max(0,min(float(h.get("start",0)),duration))
                b = max(a+1,min(float(h.get("end",a+8)),duration))
                highlights.append({"start":round(a,1),"end":round(b,1),
                  "title":str(h.get("title","আকর্ষণীয় দৃশ্য"))[:100],
                  "reason":str(h.get("reason",""))[:300],
                  "score":max(1,min(10,int(h.get("score",5))))})
            except Exception: pass
        highlights.sort(key=lambda x:x["score"],reverse=True)
        jf.write_text(json.dumps({"status":"done","duration":round(duration,1),
                                  "highlights":highlights,"progress":"বিশ্লেষণ সম্পন্ন"},ensure_ascii=False))
    except Exception as e:
        jf.write_text(json.dumps({"status":"error","error":str(e)},ensure_ascii=False))

@app.get("/",response_class=HTMLResponse)
def home():
    return (BASE/"static"/"index.html").read_text(encoding="utf-8")

@app.post("/api/upload")
async def upload(background_tasks: BackgroundTasks, video: UploadFile=File(...), api_key: str=Form("")):
    key = api_key.strip() or os.getenv("OPENAI_API_KEY","").strip()
    if not key: raise HTTPException(400,"OpenAI API key দিন অথবা সার্ভারে OPENAI_API_KEY সেট করুন।")
    suffix=Path(video.filename or "").suffix.lower()
    if suffix not in {".mp4",".mov",".mkv",".webm",".m4v",".avi"}:
        raise HTTPException(400,"MP4, MOV, MKV, WEBM, M4V বা AVI ভিডিও দিন।")
    jid=uuid.uuid4().hex[:12]; dest=UPLOADS/f"{jid}{suffix}"; size=0
    try:
        with dest.open("wb") as out:
            while True:
                chunk=await video.read(1024*1024)
                if not chunk: break
                size += len(chunk)
                if size>MAX_BYTES: raise HTTPException(413,f"সার্ভারের আপলোড সীমা {MAX_BYTES//(1024**3)} GB।")
                out.write(chunk)
    except Exception:
        dest.unlink(missing_ok=True); raise
    (JOBS/f"{jid}.json").write_text(json.dumps({"status":"queued","progress":"বিশ্লেষণের জন্য প্রস্তুত"},ensure_ascii=False))
    background_tasks.add_task(process_job,jid,dest,key)
    return {"job_id":jid}

@app.get("/api/status/{job_id}")
def status(job_id:str):
    f=JOBS/f"{job_id}.json"
    if not f.exists(): raise HTTPException(404,"কাজটি পাওয়া যায়নি।")
    return JSONResponse(json.loads(f.read_text(encoding="utf-8")))

@app.post("/api/clip/{job_id}")
def make_clip(job_id:str,payload:dict):
    source=next(iter(UPLOADS.glob(f"{job_id}.*")),None)
    if source is None: raise HTTPException(404,"মূল ভিডিও পাওয়া যায়নি।")
    start,end=float(payload.get("start",0)),float(payload.get("end",0)); duration=duration_of(source)
    if start<0 or end<=start or end>duration+0.5: raise HTTPException(400,"সময় সঠিক নয়।")
    out=CLIPS/f"{job_id}_{int(start*10)}_{int(end*10)}.mp4"
    run(["ffmpeg","-y","-ss",str(start),"-i",str(source),"-t",str(end-start),
         "-map","0:v:0","-map","0:a?","-c:v","libx264","-preset","veryfast",
         "-crf","22","-c:a","aac","-movflags","+faststart",str(out)])
    return {"download":f"/api/download/{out.name}"}

@app.get("/api/download/{filename}")
def download(filename:str):
    p=CLIPS/Path(filename).name
    if not p.exists(): raise HTTPException(404,"ক্লিপ পাওয়া যায়নি।")
    return FileResponse(p,media_type="video/mp4",filename=p.name)

@app.get("/health")
def health(): return {"ok":True}
