"""Generise `assets/mujofix.ico` (multi-size, PNG-embed) bez novih zavisnosti.

Ikona: Fluent 2 stil — zaobljeni kvadrat u akcent boji sa bijelim "lupa + kvacica"
(staklo = skeniranje, kvacica = popravljeno). Crta PySide6 QPainter, a ICO
kontejner se pise rucno (ICO podrzava PNG payload od Windows Vista).

Koristenje:  python scripts/make_icon.py [izlaz.ico]
Rezultat je commitovan u repo, pa build ne mora da ga generise.
"""

from __future__ import annotations

import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

SIZES = (16, 24, 32, 48, 64, 128, 256)
ACCENT_TOP = (0x0F, 0x6C, 0xBD)     # Fluent 2 brand (light)
ACCENT_BOTTOM = (0x0C, 0x3B, 0x5E)


def _render_png(size: int) -> bytes:
    """Nacrtaj ikonu na `size` px i vrati PNG bajtove."""
    from PySide6.QtCore import QBuffer, QIODevice, QRectF, Qt
    from PySide6.QtGui import (QBrush, QColor, QImage, QLinearGradient,
                               QPainter, QPainterPath, QPen)

    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, True)

    # zaobljeni kvadrat (Fluent "squircle" aproksimacija)
    radius = size * 0.22
    path = QPainterPath()
    path.addRoundedRect(QRectF(0.5, 0.5, size - 1, size - 1), radius, radius)
    gradient = QLinearGradient(0, 0, 0, size)
    gradient.setColorAt(0.0, QColor(*ACCENT_TOP))
    gradient.setColorAt(1.0, QColor(*ACCENT_BOTTOM))
    painter.fillPath(path, QBrush(gradient))

    white = QColor(255, 255, 255)
    # lupa: prsten
    ring_width = max(1.4, size * 0.085)
    painter.setPen(QPen(white, ring_width, Qt.SolidLine, Qt.RoundCap))
    painter.setBrush(Qt.NoBrush)
    cx, cy = size * 0.44, size * 0.42
    r = size * 0.24
    painter.drawEllipse(QRectF(cx - r, cy - r, 2 * r, 2 * r))

    # drska lupe (dijagonala ka dolje-desno)
    handle = QPen(white, ring_width * 1.15, Qt.SolidLine, Qt.RoundCap)
    painter.setPen(handle)
    start = (cx + r * 0.72, cy + r * 0.72)
    end = (size * 0.80, size * 0.80)
    painter.drawLine(int(start[0]), int(start[1]), int(end[0]), int(end[1]))

    # kvacica unutar sociva
    check = QPen(white, ring_width * 0.95, Qt.SolidLine, Qt.RoundCap)
    painter.setPen(check)
    p1 = (cx - r * 0.42, cy + r * 0.02)
    p2 = (cx - r * 0.10, cy + r * 0.36)
    p3 = (cx + r * 0.46, cy - r * 0.34)
    painter.drawLine(int(p1[0]), int(p1[1]), int(p2[0]), int(p2[1]))
    painter.drawLine(int(p2[0]), int(p2[1]), int(p3[0]), int(p3[1]))
    painter.end()

    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(buffer.data())


def write_ico(path: str, pngs: list[tuple[int, bytes]]) -> str:
    """ICO sa PNG payloadima (jedan ICONDIR + N ICONDIRENTRY + PNG blokovi)."""
    header = struct.pack("<HHH", 0, 1, len(pngs))
    offset = len(header) + 16 * len(pngs)
    entries, payloads = b"", b""
    for size, png in pngs:
        dim = 0 if size >= 256 else size  # 0 znaci 256 u ICO formatu
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32,
                               len(png), offset)
        payloads += png
        offset += len(png)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(header + entries + payloads)
    return path


def main() -> int:
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "..", "assets", "mujofix.ico")
    pngs = [(size, _render_png(size)) for size in SIZES]
    path = write_ico(os.path.abspath(out), pngs)
    print(f"napisano: {path} ({os.path.getsize(path)} B, "
          f"{len(SIZES)} velicina: {', '.join(str(s) for s in SIZES)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
