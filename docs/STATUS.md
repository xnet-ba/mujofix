# STATUS.md — stanje projekta (azurirano: 2026-10-06)

## Faza 6 — gotova kao kod (release BLOKIRAN dok VM lista ne prodje)

- `mujofix.spec` (MujoFix.exe GUI + MujoFixCLI.exe), `installer/mujofix.iss`
  (lowest privileges, deinstalacija brise sve), `OPENCODE_PIN.txt`
  (SHA-256 SE MORA popuniti prije build-a, inace CI build puca).
- `.github/workflows/ci.yml`: lint+testi (ubuntu+windows), build na tag sa
  SHA-256. CI nikad izvrsen — netestirano.
- THIRD_PARTY_NOTICES.md (OpenCode MIT, PySide6 LGPL-3.0, Python PSF).
- docs/TESTING.md: rucna VM lista (A-F) — OBAVEZNA prije tag-a.
- Repo fajlovi: README.md (HTML), README.en.md, LICENSE (MIT),
  CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, CHANGELOG (0.1.0), .editorconfig,
  Issue/PR sabloni.
- Odluka: BEZ `v0.1.0` tag-a i BEZ javnog release-a dok docs/TESTING.md ne
  bude PASS na Win10 i Win11. In-app auto-update nije implementiran
  (nadogradnja rucno preko GitHub Releases + SHA-256).

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

## Faza 5 — gotova (kod + Linux dokazi, Win VM ceka)

- network (DNS CRITICAL, TCP latencija, hosts hijack, proxy, Winsock),
  config (PATH rupe, TEMP var, power saver, CBS/SFC tragovi),
  drivers (pnputil, stariji od 8 god; nekoristeni programi se ne laziju),
  duplicates (velicina->64KB->sha256, >2GB "vjerovatno", nikad auto-brisanje),
  suspicious ("sumnjivo, razlozi", potpis, Defender samo citanje),
  permissions (UAC OFF = CRITICAL, ACL, share-ovi).
- 100/100 testova prolazi. Svi Win-specficni pozivi su mockovani;
  pravi winreg/pnputil/sc/powercfg/Getty postupci cekaju VM.

## Faza 4 — gotova (kod + Linux dokazi, Win VM + Zen ToS cekaju)

- `ai/provider.py`: apstraktan Provider (zamjenjiv Ollama/OpenAI-kompatibilnim),
  OpenCodeProvider (`run --attach`, agent mujofix), FallbackChain (retry s
  backoff-om -> sljedeci model -> offline), kompaktni kontekst (max 10 nalaza),
  `sent_log` za ekran "sta je tacno poslano", best-effort lista modela.
- `ai/sanitize.py`: anonimizacija (ime, hostname, IP/MAC, serijski, licne putanje;
  tajni kljucevi se dropaju).
- `ai/mujofix_mcp.py`: `--findings` s pravim podacima scannera (dokazan stdio
  roundtrip), validator + cap 20 koraka + prazna akcija se odbija.
- `ui/consent.py`: ekran pristanka (kategorije + primjer STVARNOG payload-a +
  NEPOTVRDJENI Zen uslovi) + SentLogViewer; default offline, izbor u QSettings.
- 77/77 testova prolazi.
- NIJE: Zen ToS i dalje neprovjeren (upisano kao nepoznato); tacke 3/4 spikea
  uz pravi model; izgled consent ekrana na Win11.

## Faza 3 — gotova (kod + Linux offscreen dokazi, Win izgled netestiran)

- `ui/main_window.py`: jedan ekran — SCAN (worker nit), sazetak, stiklirana
  lista (sve/pojedinacno/nista), tehnicki detalji na preklopnik, POPRAVI SVE,
  progres + sigurno zaustavljanje, izvjestaj, "Ponisti sve" (rollback obrnutim
  redom). UAC akcije se preskacu uz objasnjenje (elevator = Faza 6).
- `i18n/strings.py`: bs default + en struktura.
- `requirements.txt`: PySide6>=6.6. Testovi GUI-a: venv python +
  QT_QPA_PLATFORM=offscreen (3 testa: tok, fix+undo roundtrip, UAC skip).
- 57/57 testova prolazi. Izgled na Win11 (fontovi, DPI, tamni rezim) NIJE
  vidjen — treba screenshot s VM-a.

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
