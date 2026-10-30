"""ICAERUS videolarını kareye böler, YOLO etiketleriyle eşler ve 'test dışı' eğitim seti kurar.
  python veri/hazirla.py 12     → 12 test, diğerleri eğitim  (veri/egitim-12/)
  python veri/hazirla.py hepsi  → dördü de eğitim (son model)
"""
import shutil, subprocess, sys
from pathlib import Path
KOK = Path(__file__).parent
V = KOK / "icaerus/set2/depot_zenodo_2_annotations"
HEPSI = ["8", "10", "12", "13"]

def etiket_klasoru(n):
    return next((V / "YOLO1.1").glob(f"YOLO*crop_23.11.23-{n}")) / "obj_train_data"

def kareler(n):
    d = KOK / "kareler" / n
    if not d.exists():
        d.mkdir(parents=True)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(V / f"Videos/crop_23.11.23-{n}.MP4"),
                        "-q:v", "2", "-start_number", "0", str(d / "frame_%06d.jpg")], check=True)
    return d

test = sys.argv[1]
egitim = HEPSI if test == "hepsi" else [n for n in HEPSI if n != test]
dogrulama = egitim[-1:] if test == "hepsi" else [test]
cik = KOK / f"egitim-{test}"
shutil.rmtree(cik, ignore_errors=True)
for bolum, liste in (("train", egitim), ("val", dogrulama)):
    for n in liste:
        kd, ed = kareler(n), etiket_klasoru(n)
        for img in kd.glob("*.jpg"):
            lab = ed / (img.stem + ".txt")
            if not lab.exists():
                continue
            for alt, src in (("images", img), ("labels", lab)):
                hedef = cik / alt / bolum / f"v{n}_{src.name}"
                hedef.parent.mkdir(parents=True, exist_ok=True)
                hedef.symlink_to(src)
(cik / "veri.yaml").write_text(f"path: {cik}\ntrain: images/train\nval: images/val\nnames:\n  0: koyun\n")
print(cik, {b: len(list((cik / 'images' / b).glob('*'))) for b in ('train', 'val')})
