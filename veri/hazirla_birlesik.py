"""Birleşik eğitim seti: beyaz koyun (egitim-buyuk) + etiketli keçi (ICAERUS 14929694) + köpek/insan (egitim-kopek/set).
Sınıflar: 0 koyun (küçükbaş: koyun+keçi — kapıdan geçen her küçükbaş sayılır), 1 kopek, 2 insan.
  python veri/hazirla_birlesik.py   → veri/egitim-birlesik/
"""
import os
import random
import shutil
from pathlib import Path

KOK = Path(__file__).parent
cik = KOK / "egitim-birlesik"
import sys
if "--yeniden" in sys.argv:
    shutil.rmtree(cik, ignore_errors=True)   # sıfırdan kur; bayraksız çağrı mevcut sete yalnız ekler (devir paketi için)
random.seed(11)
say = {"koyun_train": 0, "koyun_val": 0, "keci_train": 0, "keci_val": 0, "kopek_train": 0, "kopek_val": 0, "r3_train": 0, "r3_val": 0, "coco_train": 0, "coco_val": 0}


def bagla(img, lab, bolum, onek):
    for alt, src in (("images", img), ("labels", lab)):
        hedef = cik / alt / bolum / f"{onek}{src.name}"
        hedef.parent.mkdir(parents=True, exist_ok=True)
        if hedef.exists():
            continue
        try:
            hedef.symlink_to(src.resolve())          # Mac/Linux
        except OSError:
            try:
                os.link(src.resolve(), hedef)        # Windows: sembolik bağ yetkisi yoksa sert bağ
            except OSError:
                shutil.copy2(src, hedef)             # son çare: kopya


# 1) beyaz koyun — mevcut büyük set (zaten train/val ayrılmış, val = 428 nadir foto)
#    Devir paketinde (egitim-birlesik.tar) bu set zaten çözümlenmiş halde gelir; egitim-buyuk yoksa atlanır.
B = KOK / "egitim-buyuk"
if B.exists():
    for bolum in ("train", "val"):
        for img in (B / "images" / bolum).iterdir():
            lab = B / "labels" / bolum / (img.stem + ".txt")
            if lab.exists():
                bagla(img, lab, bolum, ""); say[f"koyun_{bolum}"] += 1

# 2) keçi — CVAT YOLO dışa aktarımı: <video>/images/*.jpg + <video>/obj_train_data/*.txt (sınıf 0 = sheep → bizde de 0)
K = KOK / "icaerus/set-keci/icerik/Annotated_Goat_Dataset"
for vdir in (sorted(K.iterdir()) if K.exists() else []):
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

# 4) 3. tur sözde etiketler — veri/sozde_etiket.py çıktısı (varsa)
R = KOK / "egitim-r3/set"
if (R / "images").exists():
    for bolum in ("train", "val"):
        for img in (R / "images" / bolum).glob("*.jpg"):
            lab = R / "labels" / bolum / (img.stem + ".txt")
            if lab.exists():
                bagla(img, lab, bolum, "r3_"); say[f"r3_{bolum}"] += 1

# 5) COCO 'sheep' — yerden/yandan çekilmiş fotoğraflar (her açıdan çalışma hedefi), veri/coco_koyun_indir.py çıktısı (varsa)
C = KOK / "coco-koyun"
if (C / "images").exists():
    for bolum in ("train", "val"):
        for img in (C / "images" / bolum).glob("*.jpg"):
            lab = C / "labels" / bolum / (img.stem + ".txt")
            if lab.exists():
                bagla(img, lab, bolum, ""); say[f"coco_{bolum}"] += 1

(cik / "veri.yaml").write_text(
    f"path: {cik.resolve()}\ntrain: images/train\nval: images/val\nnames:\n  0: koyun\n  1: kopek\n  2: insan\n")
print(say)
print("toplam train", sum(v for k, v in say.items() if k.endswith("train")), "val", sum(v for k, v in say.items() if k.endswith("val")))
