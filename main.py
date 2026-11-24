import os, zlib, struct, binascii

W = H = 1024
BG = (247, 243, 234)
INK = (20, 20, 20)
RED = (179, 39, 30)

# 5x7 bitmap font. Each glyph is 7 rows of 5 bits, one base-32 char per row.
A = "0123456789ABCDEFGHIJKLMNOPQRSTUV"
O = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .%$-+!?'/():"
F = "EHHVHHHUHHUHHUFGGGGGFUHHHHHUVGGUGGVVGGUGGGFGGNHHEHHHVHHHV44444V72222ICHIKOKIHGGGGGGVHRLLHHHHPLJHHHEHHHHHEUHHUGGGEHHHLIDUHHUKIHFGGE11UV444444HHHHHHEHHHHHA4HHHLLRHHHA4AHHHHA4444V1248GVEJLPHHE4C4444EEH1248VU11E11U26AIV22VGU11HEEGGUHHEV124444EHHEHHEEHHF11E00000000000066OO248334FLELF4000E000044E4404444404EH124044480000122488G248884284222480660660"
G = {c: [A.find(F[i * 7 + r]) for r in range(7)] for i, c in enumerate(O)}

px = bytearray(bytes(BG) * (W * H))


def rect(x, y, w, h, c):
    b = bytes(c)
    for yy in range(y, y + h):
        o = (yy * W + x) * 3
        px[o:o + w * 3] = b * w


def tw(s, sc):
    return len(s) * 6 * sc - sc


def text(s, x, y, sc, c):
    s = s.upper()
    for ch in s:
        g = G.get(ch)
        if g:
            for r, v in enumerate(g):
                for b in range(5):
                    if v >> (4 - b) & 1:
                        rect(x + b * sc, y + r * sc, sc, sc, c)
        x += 6 * sc


def ctext(s, x, y, w, sc, c):
    text(s, x + (w - tw(s, sc)) // 2, y, sc, c)


def wrap(s, maxw, sc):
    ls, cur = [], ""
    for wd in s.split(" "):
        t = wd if not cur else cur + " " + wd
        if tw(t, sc) <= maxw:
            cur = t
        else:
            if cur:
                ls.append(cur)
            cur = wd
    if cur:
        ls.append(cur)
    return ls


def block(s, x, y, maxw, sc, c, lh, center=False):
    ls = wrap(s, maxw, sc)
    for i, ln in enumerate(ls):
        if center:
            ctext(ln, x, y + i * lh, maxw, sc, c)
        else:
            text(ln, x, y + i * lh, sc, c)
    return len(ls)


def fit(s, maxw, maxh):
    sc = maxh // 7
    while sc > 1 and tw(s, sc) > maxw:
        sc -= 1
    return sc


# ---------- masthead ----------
ctext("THE WORLD", 0, 26, W, 11, INK)
ctext("MONDAY 23 NOVEMBER 2026", 0, 108, W, 3, INK)
rect(24, 136, 976, 5, INK)
rect(24, 145, 976, 2, RED)

# ---------- lead: COP31 ----------
ctext("NO DEAL", 0, 158, W, 16, RED)
ctext("COP31 COLLAPSES IN ANTALYA", 0, 278, W, 6, INK)
block("EU REJECTS A TEXT SILENT ON FOSSIL FUELS AS THE LONGEST COP ON RECORD ENDS WITH NO DEAL",
      24, 328, 976, 3, INK, 26, center=True)
ctext("190+ COUNTRIES - FIRST NO-DEAL COP SINCE 2009", 0, 388, W, 3, RED)

# ---------- grid rules ----------
rect(24, 418, 976, 2, INK)
rect(24, 656, 976, 2, INK)
rect(510, 426, 2, 460, INK)

# ---------- grid cells: (big, headline, dek, x, y) ----------
cells = [
    ("7 DRONES", "UKRAINE SINKS RUSSIAN WARSHIP",
     "Drones sink the corvette Merkury off Libya.", 24, 426),
    ("+31%", "HUANG IS BACK AND NVIDIA SOARS",
     "Shares soar 31% as Huang returns to lead Nvidia.", 522, 426),
    ("24 DEAD", "SWEETS FACTORY FIRE IN INDONESIA",
     "Fire at a sweets factory in Banten. 30 missing.", 24, 660),
    ("$1.62BN", "INDIA BACKS NEPAL REBUILD",
     "Modi announces the aid after talks with PM Shah.", 522, 660),
]
for big, head, dek, cx, cy in cells:
    sc = fit(big, 450, 68)
    text(big, cx + 12, cy + 12, sc, RED)
    n = block(head, cx + 12, cy + 12 + 68 + 8, 450, 4, INK, 36)
    block(dek, cx + 12, cy + 12 + 68 + 8 + n * 36 + 6, 450, 3, INK, 24)

# ---------- bottom strip: Kyiv ----------
rect(24, 888, 976, 2, INK)
text("15", 24, 905, 12, RED)
text("KILLED IN STRIKES ON KYIV REGION", 176, 905, 4, INK)
block("Russian strikes hit the Kyiv region. 11 die as a block of flats falls in Dymer.",
      176, 937, 824, 3, INK, 24)

# ---------- write PNG ----------
def chunk(t, d):
    return struct.pack(">I", len(d)) + t + d + struct.pack(">I", binascii.crc32(t + d) & 0xffffffff)


raw = b"".join(b"\x00" + bytes(px[y * W * 3:(y + 1) * W * 3]) for y in range(H))
png = (b"\x89PNG\r\n\x1a\n"
       + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(raw, 9))
       + chunk(b"IEND", b""))
os.makedirs("/output", exist_ok=True)
open("/output/entry.png", "wb").write(png)
