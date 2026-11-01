"""Modelin sınıf haritasına göre hangi sınıf sayılır, hangileri yalnız gösterilir.
- Bizim eğitim: 0 koyun (küçükbaş), 1 kopek, 2 insan  → sayılan 0; 1-2 ekranda etiketlenir, sayılmaz
- Eski tek sınıflı ince ayar: 0 koyun
- Hazır COCO modeli: 18 sheep
"""


def koyun_sinifi(model):
    adlar = {int(k): str(v) for k, v in model.names.items()}
    if adlar.get(0) == "koyun" or len(adlar) == 1:
        return 0
    return 18


def izlenecek_siniflar(model):
    """Tespit edilecek sınıflar (sayılan + ekranda gösterilen)."""
    adlar = {int(k): str(v) for k, v in model.names.items()}
    if adlar.get(0) == "koyun" and len(adlar) > 1:
        return list(adlar.keys())          # koyun + köpek + insan
    return [koyun_sinifi(model)]


ETIKET = {1: "KOPEK", 2: "INSAN"}
RENK = {1: (0, 0, 255), 2: (255, 120, 0)}   # BGR: köpek kırmızı, insan mavi
