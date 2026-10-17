# Changelog (semantičko verzioniranje; `mujofix.spec` čita vrh ovog fajla)

## [Unreleased]
### Dodano
- Auto-fix: `quarantine_duplicates` (potvrđeni sha256 duplikati u karantin, jedna kopija ostaje).
- Elevacija: gumb "Pokreni kao administrator" + izvršavanje `needs_elevation`
  akcija kad je proces admin (`windows.is_admin`/`relaunch_elevated`).
### Napomene
- Elevator (pravi UAC prompt) i Win izgled ostaju netestirani na VM-u.

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
- Potvrđeno host-direct na pravom Windows 11 računaru: scan 9/9 scannera /
  0 skipped, 5/5 akcija s identičnim rollback-om, GUI smoke, spike 1–2.
- 104/104 unit testa; CI zelen (Ubuntu + Windows).
- Puna Win10 + Win11 VM matrica ostaje opciona (docs/TESTING.md).
- Build NIJE potpisan; SmartScreen upozorenje je očekivano.
