"""Dò khung truyện theo lề trắng: cắt ngang theo dải hàng trắng, rồi mỗi dải cắt dọc theo cột trắng."""
import json, sys
import numpy as np
from PIL import Image
def runs(mask, minlen):
    out, s = [], None
    for i, v in enumerate(list(mask) + [False]):
        if v and s is None: s = i
        if not v and s is not None:
            if i - s >= minlen: out.append((s, i))
            s = None
    return out
def panels(path):
    im = np.asarray(Image.open(path).convert("L")).astype(np.float32); H, W = im.shape
    white = im > 235
    rows = white.mean(1) > 0.97
    bands = [(a, b) for a, b in runs(~rows, int(H * 0.04))]
    res = []
    for y0, y1 in bands:
        cols = white[y0:y1].mean(0) > 0.97
        for x0, x1 in runs(~cols, int(W * 0.08)):
            res.append({"x": x0 / W, "y": y0 / H, "w": (x1 - x0) / W, "h": (y1 - y0) / H})
    return res
if __name__ == "__main__":
    for p in sys.argv[1:]:
        r = panels(p); print(p, len(r)); [print("  ", {k: round(v, 3) for k, v in q.items()}) for q in r]
