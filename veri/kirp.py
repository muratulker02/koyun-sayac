"""Demo videolarının başındaki/sonundaki koyunsuz boşluğu kırpar (1 sn pay). Sayıyı etkilemez: koyun olmayan kısım gider."""
import json, subprocess, sys
from pathlib import Path
from ultralytics import YOLO
KOK = Path(__file__).resolve().parent.parent
m = YOLO(str(KOK / "modeller" / "koyun-tepeden.pt"))
D = json.load(open(KOK / "test-video" / "demolar.json"))
for ad in D:
    v = KOK / "test-video" / ad
    if not v.exists(): continue
    fps = float(subprocess.check_output(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=r_frame_rate","-of","csv=p=0",str(v)]).decode().strip().split("/")[0]) / max(1, float(subprocess.check_output(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=r_frame_rate","-of","csv=p=0",str(v)]).decode().strip().split("/")[1]))
    sure = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(v)]).decode().strip())
    ilk = son = None; k = 0; adim = 3
    for r in m.predict(source=str(v), stream=True, imgsz=640, conf=0.3, vid_stride=adim, verbose=False):
        if len(r.boxes) >= 1:
            t = k * adim / fps
            if ilk is None: ilk = t
            son = t
        k += 1
    if ilk is None:
        print(f"{ad}: koyun bulunamadı, dokunulmadı"); continue
    bas, bit = max(0, ilk - 1.0), min(sure, son + 1.0)
    if bas < 1.5 and sure - bit < 1.5:
        print(f"{ad}: boşluk yok ({sure:.0f} sn)"); continue
    tmp = v.with_name(v.stem + ".kirp.mp4")
    subprocess.run(["ffmpeg","-v","error","-y","-ss",f"{bas:.2f}","-to",f"{bit:.2f}","-i",str(v),"-c:v","libx264","-preset","veryfast","-crf","20","-an",str(tmp)], check=True)
    tmp.replace(v)
    print(f"{ad}: {sure:.0f} sn → {bit-bas:.0f} sn (baştan {bas:.1f} sn, sondan {sure-bit:.1f} sn kırpıldı)")
