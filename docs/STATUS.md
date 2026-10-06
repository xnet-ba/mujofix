# STATUS.md — stanje projekta (azurirano: 2026-10-06)

## Faza 0 SPIKE — djelimicno gotovo (kod + Linux dokazi, Win VM ceka)

Uradjeno (Faza 0):
- `mujofix/ai/opencode_runtime.py` — `opencode serve` child: 127.0.0.1,
  slucajan port, slucajna lozinka po pokretanju, siguran close().
- `mujofix/ai/agent_config.py` — agent `mujofix` (deny: shell/edit/write/patch/
  webfetch/websearch/task; update disable; share manual) + offline fallback.
- `mujofix/ai/mujofix_mcp.py` — stdio MCP: 5 alata, `propose_plan` validira
  prema allowlisti od 3 akcije + odbija zasticene zone (System32, WinSxS...).
- `scripts/phase0_spike.py` — 5 provjera, PASS/SKIP/FAIL, exit kod.
- `tests/test_phase0_spike.py` — 16 unit testova.

Testirano (sve prolazi):
- 16/16 unit testova (`python3 -m unittest discover -s mujofix/tests`).
- Zivi smoke na Linuxu: CHECK 1 PASS (binary 1.18.34 bez Node-a),
  CHECK 2 PASS (serve na 127.0.0.1, auth obavezan), CHECK 5 PASS,
  CHECK 3/4 SKIP (nema modela) — bez zaostalih procesa.

NIJE testirano (potreban cist Win10 + Win11 VM):
- Tacke 3 i 4 uz pravi Zen model; bundlovana kopija u installeru;
  SHA-256 provjera; izolacija config/data direktorija pinovane verzije.

Nepoznato (upisati prije Faze 4, ne pretpostavljati):
- OpenCode Zen ToS: cuvanje/koristenje podataka s besplatnog nivoa.
- Tacan API za listu besplatnih modela (providers/models) uz pinovanu verziju.
- Koja pinovana OpenCode verzija ide u installer (trenutno dokazano: 1.18.34).

Sljedece: pokrenuti `scripts/phase0_spike.py --model <zen-model>` na Win10
i Win11 VM-u. Ako tacka 3/4 ne prodje: alternativa je direktni
OpenAI-kompatibilni Zen endpoint kroz vlastiti provider interfejs.

## GitHub (2026-10-06)

Repo ziv: https://github.com/xnet-ba/mujofix (public, main).
Pristup: SSH kljuc `mujofix-agent` (trajan) + token koristen jednom za
kreiranje repoa. Push ide preko `origin` (SSH).

## Faza 2 — gotova (kod + Linux dokazi, Win VM ceka)

- `actions/base.py`: Action ugovor (precondition/snapshot/apply/verify/rollback),
  Runner (pad nakon snapshot-a -> rollback), dry-run, karantin, audit log.
- 3 akcije: disable_startup_item (HKCU/HKLM, UAC samo za HKLM),
  clean_temp (starije od 7 dana u karantin, manifest), restart_service (`sc`,
  treba UAC, rizik srednji).
- Svaka akcija: test apply -> verify -> rollback -> stanje identicno originalu.
- 54/54 testova prolazi.

## Faza 1 — gotovo (kod + Linux dokazi, Win VM ceka)

- `core/models.py`: Finding (obavezan evidence, CRITICAL/MEDIUM/LOW) + ScanReport.
- `platform/windows.py`: verzija/build detekcija, winreg wrapperi (stdlib).
- `scanners/base.py`: interfejs, ScanContext(cancel), registry; greska = skipped.
- Scanneri: startup (Run/RunOnce + Startup folderi), disk (prostor + temp +
  WU kes + Windows.old), services (Get-Service auto/stopped).
- `cli.py`: `scan` (JSON) + `--summary` (obican jezik).
- 34/34 testova prolazi; zivi `scan --summary` na Linuxu radi
  (disk nadje, startup/services se graceful preskoce).
