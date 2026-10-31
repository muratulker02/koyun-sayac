"""Birleşik eğitim seti: beyaz koyun (egitim-buyuk) + etiketli keçi (ICAERUS 14929694) + köpek/insan (egitim-kopek/set).
Sınıflar: 0 koyun (küçükbaş: koyun+keçi — kapıdan geçen her küçükbaş sayılır), 1 kopek, 2 insan.
  python veri/hazirla_birlesik.py   → veri/egitim-birlesik/
"""
import random
import shutil
from pathlib import Path

KOK = Path(__file__).parent
cik = KOK / "egitim-birlesik"
shutil.rmtree(cik, ignore_errors=True)
random.seed(11)
say = {"koyun_train": 0, "koyun_val": 0, "keci_train": 0, "keci_val": 0, "kopek_train": 0, "kopek_val": 0}


def bagla(img, lab, bolum, onek):
    for alt, src in (("images", img), ("labels", lab)):
        hedef = cik / alt / bolum / f"{onek}{src.name}"
        hedef.parent.mkdir(parents=True, exist_ok=True)
        if not hedef.exists():
            hedef.symlink_to(src.resolve())


# 1) beyaz koyun — mevcut büyük set (zaten train/val ayrılmış, val = 428 nadir foto)
B = KOK / "egitim-buyuk"
for bolum in ("train", "val"):
    for img in (B / "images" / bolum).iterdir():
        lab = B / "labels" / bolum / (img.stem + ".txt")
        if lab.exists():
            bagla(img, lab, bolum, ""); say[f"koyun_{bolum}"] += 1

# 2) keçi — CVAT YOLO dışa aktarımı: <video>/images/*.jpg + <video>/obj_train_data/*.txt (sınıf 0 = sheep → bizde de 0)
K = KOK / "icaerus/set-keci/icerik/Annotated_Goat_Dataset"
for vdir in sorted(K.iterdir()):
    d = vdir / "obj_train_data"
    if not d.is_dir():
        continue
    for img in sorted((vdir / "images").glob("*.jpg")):
        lab = d / (img.stem + ".txt")
        if not lab.exists():
            continue
        bolum = "val" if random.random() < 0.15 else "train"
        bagla(img, lab, bolum, f"keci_{vdir.name[:20]}_"); say[f"keci_{bolum}"] += 1

# 3) köpek + insan (+ koyun) — hazirla_kopek.py çıktısı (varsa)
D = KOK / "egitim-kopek/set"
if (D / "images").exists():
    for bolum in ("train", "val"):
        for img in (D / "images" / bolum).glob("*.jpg"):
            lab = D / "labels" / bolum / (img.stem + ".txt")
            if lab.exists():
                bagla(img, lab, bolum, "kp_"); say[f"kopek_{bolum}"] += 1

(cik / "veri.yaml").write_text(
    f"path: {cik.resolve()}\ntrain: images/train\nval: images/val\nnames:\n  0: koyun\n  1: kopek\n  2: insan\n")
print(say)
print("toplam train", sum(v for k, v in say.items() if k.endswith("train")), "val", sum(v for k, v in say.items() if k.endswith("val")))
