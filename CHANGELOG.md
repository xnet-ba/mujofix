# Changelog (semantičko verzioniranje; `mujofix.spec` čita vrh ovog fajla)

## [0.1.0] - 2026-10-06
### Dodano
- Faza 0: OpenCode runtime (127.0.0.1 + lozinka), agent `mujofix`, MCP stub, spike skripta.
- Faza 1: model nalaza s evidence, 3 scannera (startup, disk, servisi), CLI `scan`.
- Faza 2: action katalog + Runner (snapshot/verify/rollback, dry-run, karantin, audit).
- Faza 3: PySide6 GUI (sažetak, odobravanje, progres, izvještaj, poništi sve), i18n bs/en.
- Faza 4: provider interfejs + fallback lanac, anonimizacija, MCP pravi podaci, pristanak.
- Faza 5: preostalih 6 scannera (mreža, konfiguracija, drajveri, duplikati, sumnjivi, permisije).
- Faza 6: PyInstaller spec, Inno Setup, CI, pravne napomene, ručna VM lista.
### Napomene
- Pre-alpha: NIŠTA nije potvrđeno na pravom Windowsu (sve čeka docs/TESTING.md).
- Nema potpisanog build-a; nema javnog release-a dok VM lista ne prođe.
