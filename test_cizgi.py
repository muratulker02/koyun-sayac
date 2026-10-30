from cizgi import CizgiSayaci

# Dikey çizgi x=100; soldan sağa yürüyen = çıkış (a yukarıda, b aşağıda)
A, B = (100, 0), (100, 200)


def yuru(s, tid, xs, y=100):
    for x in xs:
        s.guncelle(tid, (x, y))


def test_tek_cikis():
    s = CizgiSayaci(A, B)
    yuru(s, 1, [50, 90, 110, 150])
    assert (s.cikan, s.giren) == (1, 0)


def test_tek_giris():
    s = CizgiSayaci(A, B)
    yuru(s, 1, [150, 110, 90, 50])
    assert (s.cikan, s.giren) == (0, 1)


def test_salinma_cift_sayilmaz():
    s = CizgiSayaci(A, B)
    yuru(s, 1, [90, 110, 95, 105, 90, 120])
    assert (s.cikan, s.giren) == (1, 0)


def test_geri_donen_sifirlanir():
    s = CizgiSayaci(A, B)
    yuru(s, 1, [90, 110, 90])
    assert (s.cikan, s.giren) == (0, 0)


def test_cizgi_disindan_gecen_sayilmaz():
    s = CizgiSayaci(A, B)
    yuru(s, 1, [90, 110], y=300)
    assert (s.cikan, s.giren) == (0, 0)


def test_yon_ters():
    s = CizgiSayaci(A, B, yon_ters=True)
    yuru(s, 1, [50, 150])
    assert (s.cikan, s.giren) == (0, 1)


def test_cok_hayvan():
    s = CizgiSayaci(A, B)
    for tid in range(700):
        yuru(s, tid, [80, 120])
    yuru(s, 9999, [120, 80])
    assert (s.cikan, s.giren) == (700, 1)
