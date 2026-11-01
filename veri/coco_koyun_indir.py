"""COCO 2017 'sheep' sınıfı (yerden/yandan çekilmiş ~1.500 fotoğraf, CC BY 4.0) → YOLO etiketli set.
Her açıdan çalışma hedefi için yandan/yerden görüntü kaynağı. Çıktı: veri/coco-koyun/{images,labels}/{train,val}
  python veri/coco_koyun_indir.py
"""
import json, io, zipfile, urllib.request, concurrent.futures, random
from pathlib import Path
KOK = Path(__file__).resolve().parent / "coco-koyun"
for d in ("images/train", "images/val", "labels/train", "labels/val"):
    (KOK / d).mkdir(parents=True, exist_ok=True)
ann_zip = KOK / "annotations_trainval2017.zip"
if not ann_zip.exists():
    print("etiket arşivi iniyor (241 MB)...", flush=True)
    urllib.request.urlretrieve("http://images.cocodataset.org/annotations/annotations_trainval2017.zip", ann_zip)
random.seed(3); toplam = 0
with zipfile.ZipFile(ann_zip) as z:
    for bolum in ("val2017", "train2017"):
        d = json.load(z.open(f"annotations/instances_{bolum}.json"))
        sheep = next(c["id"] for c in d["categories"] if c["name"] == "sheep")
        img = {i["id"]: i for i in d["images"]}
        kutular = {}
        for a in d["annotations"]:
            if a["category_id"] == sheep and not a.get("iscrowd", 0):
                kutular.setdefault(a["image_id"], []).append(a["bbox"])
        print(bolum, "koyunlu görüntü:", len(kutular), flush=True)
        def indir(iid):
            i = img[iid]; w, h = i["width"], i["height"]
            hedef_bolum = "val" if random.random() < 0.1 else "train"
            jp = KOK / "images" / hedef_bolum / f"coco_{i['file_name']}"
            if not jp.exists():
                try:
                    urllib.request.urlretrieve(i["coco_url"], jp)
                except Exception as e:
                    return 0
            satir = [f"0 {(x+bw/2)/w:.6f} {(y+bh/2)/h:.6f} {bw/w:.6f} {bh/h:.6f}" for x, y, bw, bh in kutular[iid]]
            (KOK / "labels" / hedef_bolum / f"coco_{Path(i['file_name']).stem}.txt").write_text("\n".join(satir) + "\n")
            return 1
        with concurrent.futures.ThreadPoolExecutor(16) as ex:
            toplam += sum(ex.map(indir, kutular))
(KOK / "veri.yaml").write_text(f"path: {KOK}\ntrain: images/train\nval: images/val\nnames:\n  0: koyun\n  1: kopek\n  2: insan\n")
print("BITTI görüntü:", toplam)
