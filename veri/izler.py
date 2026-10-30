"""ICAERUS gt.txt izlerini videonun ilk karesi üstüne çizer (yön/çizgi seçimi için)."""
import sys, cv2, collections
vid, gt, out = sys.argv[1:4]
cap = cv2.VideoCapture(vid); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); fps = cap.get(cv2.CAP_PROP_FPS)
ok, img = cap.read()
iz = collections.defaultdict(list)
for s in open(gt):
    f, i, x, y, w, h = s.split(",")[:6]
    iz[int(i)].append((int(f), float(x) + float(w) / 2, float(y) + float(h) / 2))
for i, p in iz.items():
    p.sort()
    for a, b in zip(p, p[1:]):
        cv2.line(img, (int(a[1]), int(a[2])), (int(b[1]), int(b[2])), (0, 255, 255), 3)
    cv2.circle(img, (int(p[0][1]), int(p[0][2])), 10, (0, 255, 0), -1)
    cv2.circle(img, (int(p[-1][1]), int(p[-1][2])), 10, (0, 0, 255), -1)
cv2.putText(img, f"{vid.split('/')[-1]} kare={n} fps={fps:.1f} iz={len(iz)}", (20, 60), 0, 1.6, (255, 255, 255), 4)
cv2.imwrite(out, cv2.resize(img, (480, 360)))
