"""Büyük eğitim seti: ICAERUS set6 (809 drone fotoğrafı, 18k kutu) + video kareleri (8,10,13).
Video 12 eğitime GİRMEZ (sayım sınavı için). Doğrulama: set6/test/Nadir_only (428 tepeden foto).
  python veri/hazirla_buyuk.py   → veri/egitim-buyuk/
"""
import shutil
from pathlib import Path

KOK = Path(__file__).parent
S6 = KOK / "icaerus/set6/dataset_11_images_avec_annotations"
KARELER = KOK / "kareler"
V = KOK / "icaerus/set2/depot_zenodo_2_annotations"
cik = KOK / "egitim-buyuk"
shutil.rmtree(cik, ignore_errors=True)


def bagla(img, lab, bolum, onek):
    for alt, src in (("images", img), ("labels", lab)):
        hedef = cik / alt / bolum / f"{onek}{src.name}"
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.symlink_to(src.resolve())


say = {"train": 0, "val": 0}
# set6 all → train
for img in (S6 / "all/images").iterdir():
    lab = S6 / "all/labels" / (img.stem + ".txt")
    if lab.exists():
        bagla(img, lab, "train", "s6_"); say["train"] += 1
# video kareleri 8,10,13 → train (12 hariç)
for n in ("8", "10", "13"):
    ed = next((V / "YOLO1.1").glob(f"YOLO*crop_23.11.23-{n}")) / "obj_train_data"
    for img in (KARELER / n).glob("*.jpg"):
        lab = ed / (img.stem + ".txt")
        if lab.exists():
            bagla(img, lab, "train", f"v{n}_"); say["train"] += 1
# set6 Nadir_only → val
for img in (S6 / "test/Nadir_only/images").iterdir():
    lab = S6 / "test/Nadir_only/labels" / (img.stem + ".txt")
    if lab.exists():
        bagla(img, lab, "val", "t_"); say["val"] += 1

(cik / "veri.yaml").write_text(f"path: {cik}\ntrain: images/train\nval: images/val\nnames:\n  0: koyun\n")
print(cik, say)
