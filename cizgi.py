"""Sanal çizgi geçiş mantığı (YOLO'dan bağımsız, test edilebilir).

Her takip id'si için merkez noktasının çizginin hangi tarafında olduğu izlenir.
Taraf değişip geçiş noktası çizgi parçasının üstündeyse geçiş sayılır.
Aynı hayvan ileri-geri salınırsa net sayım bozulmaz: her id'nin katkısı
yalnızca son durumuna göre (-1, 0, +1) hesaplanır.
"""


def _taraf(p, a, b):
    # a->b doğrusuna göre p'nin işareti (+ sol / - sağ)
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


def _kesisir(p1, p2, a, b):
    d1, d2 = _taraf(p1, a, b), _taraf(p2, a, b)
    d3, d4 = _taraf(a, p1, p2), _taraf(b, p1, p2)
    return (d1 * d2 < 0) and (d3 * d4 < 0)


class CizgiSayaci:
    """a->b çizgisi. Sol taraftan (+) sağa (-) geçiş = 'cikis', tersi = 'giris'.

    Yön ters gelirse yon_ters=True verilir.
    """

    def __init__(self, a, b, yon_ters=False):
        self.a, self.b = a, b
        self.yon_ters = yon_ters
        self.son_nokta = {}   # id -> son merkez
        self.katki = {}       # id -> net katkı (+1 çıktı, -1 girdi, 0)

    def guncelle(self, tid, nokta):
        onceki = self.son_nokta.get(tid)
        self.son_nokta[tid] = nokta
        if onceki is None or not _kesisir(onceki, nokta, self.a, self.b):
            return None
        sol_dan_saga = _taraf(onceki, self.a, self.b) > 0
        cikis = sol_dan_saga != self.yon_ters
        k = self.katki.get(tid, 0) + (1 if cikis else -1)
        self.katki[tid] = max(-1, min(1, k))
        return "cikis" if cikis else "giris"

    @property
    def cikan(self):
        return sum(1 for k in self.katki.values() if k > 0)

    @property
    def giren(self):
        return sum(1 for k in self.katki.values() if k < 0)
