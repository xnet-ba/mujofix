# STATUS.md — stanje projekta (azurirano: 2026-10-18)

## Aplikacija zavrsena (kod + host dokazi; 2026-10-17)

- Faze 0-6 su kompletne u kodu. Nema TODO/FIXME/stub-ova u `mujofix/`.
- Potvrdjeno host-direct na pravom Windows 11 (laptop, High integrity token):
  scan 9/9 scannera / 0 skipped, 5/5 akcija s identicnim rollback-om
  (`scripts/host_proof.py`), GUI smoke, spike 1-2 (opencode 1.18.34 bez Node-a,
  serve samo 127.0.0.1 + lozinka). Detalji nize u "Ryzen lab".
- 104/104 unit testa; CI zelen (Ubuntu + Windows).
- `installer/OPENCODE_PIN.txt` POPUNJEN (v1.18.34, SHA-256 windows-x64) —
  build kapija u CI-ju nije vise blokirana.
- Tag `v0.1.0` pushnut (2026-10-17): CI build ZELEN (2x: run #37, pa #38
  nakon `ci:` izmjene) — pin provjera, OpenCode download + SHA-256, PyInstaller
  build, bundlovanje OpenCode-a, SHA-256 sums, i SMOKE TEST bundlovanog
  `MujoFixCLI.exe` (`scan --summary`) na windows-latest: sve PASS.
- CI sada automatski OBJAVLJUJE GitHub Release na svaki `v*` tag
  (`.github/workflows/ci.yml`, `gh release create` + `contents: write`).
- GitHub Release `v0.1.0` OBJAVLJEN (puni, ne draft): asset
  `MujoFix-v0.1.0.zip` (~114 MB) + `SHA256SUMS.txt`.
  https://github.com/xnet-ba/mujofix/releases/tag/v0.1.0
- ODLUKA: puna Win10 + Win11 VM matrica (docs/TESTING.md) je OPCIONA produzena
  validacija, ne tvrda kapija. Release ide nepotpisan (SmartScreen ocekivan).
- RIJESENO 2026-10-18 (Issue #4): Zen ToS/privatnost besplatne razine
  POTVRDJENI iz primarnih izvora (ToS eff. 2026-08-15: za neplacene racune
  sadrzaj se smije koristiti za unapredjenje usluge; Zen docs: provajderi
  uglavnom zero-retention, ali pojedini besplatni modeli tokom promo perioda
  koriste podatke za poboljsanje modela, NVIDIA endpointi se loguju,
  OpenAI/Anthropic se cuvaju 30 dana). Consent tekst + README azurirani sa
  "NEPOTVRDJENI" na konkretnu tvrdnju + izvori; test cuva to stanje.
- Otvoreno (nije blokada): potpisivanje koda, VM validacija stvarnog Windows
  izvrsavanja (bez UAC/VM okruzenja). Issue #2 (UAC elevator + auto-update) je
  implementiran kao kod.
- POPRAVLJENO 2026-10-18: `ai/provider.py:free_zen_models` je filtrirao po
  podstringu "zen", a Zen modeli su `opencode/<id>` → vracao je prazno. Sada
  filtrira po stvarnom prefiksu `opencode/` + "-free" marker, uz izricitu listu
  besplatnih stealth modela (`big-pickle`); nepoznat `opencode/*` (moguce
  placen) se ne vraca. Dokaz: `opencode models` (pinovani) → 10/415 pogodaka,
  tacno besplatni Zen modeli. Test `test_free_zen_filter` koristi prave ID-jeve.
- ISPRAVLJENO 2026-10-18 (kriticno, dokazano protiv pinovanog binarnog):
  `ai/agent_config.py` je pisan po V2 dokumentaciji (`agents` + `permissions`
  lista, `mcp.servers`), a pinovani opencode je V1 i takav config ODBIJA:
  `GET /config` → 400 `ConfigInvalidError`, "V2 permissions are not supported
  by OpenCode V1" → cijeli zivi put bi pao pri startu. Sada V1 oblik:
  `mcp` mapa (`mujofix`), `agent` (jednina), `prompt`, `tools` mapa sa svim
  ugrađenim alatima `false` + `mcp_*: true`. Imena alata uzeta iz pinovanog
  `opencode agent create --help` (bash, read, edit, glob, grep, webfetch, task,
  todowrite, websearch, lsp, skill) — stari `shell`/`write`/`patch` ne postoje
  kao alati. Dokaz: novi integracioni test digne stvarni `opencode serve` sa
  upisanim configom i tvrdi 200 + `agent.mujofix` + `permission` deny
  (bash/edit/webfetch/websearch/task), preskace se bez binarnog. Zasto je
  `mcp_*` izricito `true`: globalni default je `ask`, a neinteraktivni `run`
  ne moze dobiti odobrenje. Ukupno 153 testa, OK.
- IMPLEMENTIRANO 2026-10-18 (zivi AI put, Issue #1 ostatak): `ExplainWorker`
  (QThread) gradi lanac van GUI niti; `build_chain`/`LiveSession` u
  `ai/provider.py` dizu `opencode serve` samo uz pristanak i gase ga na
  zatvaranju prozora (`closeEvent` + `close()` pri novom objasnjenju).
  Svaki kvar (nema binary-ja, server, besplatni model) → offline lanac + iskren
  razlog u logu. Testovi: 6 novih (5 Qt-free u test_faza4a, 1 GUI lifecycle u
  test_faza4c); ukupno 149 (+2 za V1 config +2 za _cmd = 153). netestirano: zivi put nije
  pokrenut na Windows VM-u (nema UAC/VM okruzenja, ne trosi se mreza).
- ISPRAVLJENO 2026-10-18 (privatnost — obecanje je bilo neistinito):
  `compact_findings` bira polja ali NE anonimizira, a `_prompt` je slao bas te
  nalaze; `sanitize` se zvao SAMO za `sent_log`. Posljedica: sirovi
  `C:\Users\<ime>\...`, IP, MAC i serijski brojevi isli su modelu dok je ekran
  "sto je poslano" prikazivao ociscenu kopiju (podcjenjivao stvarnost) —
  suprotno tekstu pristanka ("Anonimizacija prije slanja"). Sada se
  anonimizacija radi JEDNOM na ulazu u `FallbackChain.explain`, pa provider i
  log vide isti payload (`log == poslano` po konstrukciji). Testovi:
  `TestFallbackChainSanitizesPayload` (model ne vidi ime/IP/MAC/tajnu; log
  jednak poslanom). Ukupno 162 testa, OK.
- ISPRAVLJENO 2026-10-18 (sigurnosno, dokazano protiv pinovanog binarnog):
  agent je bio `mode: "subagent"`, a `opencode run --agent mujofix` tada TIHO
  odbaci nas agent i nastavi sa DEFAULT agentom (puni pristup): "agent
  "mujofix" is a subagent, not a primary agent. Falling back to default agent".
  Sada `mode: "all"` — `run --agent mujofix` ostaje na nasem agentu (dokaz:
  probe sa sve tri vrijednosti; `primary` i `all` bez upozorenja, `subagent`
  sa upozorenjem). Test: `test_mode_is_not_subagent`. Ukupno 160 testa, OK.
- ISPRAVLJENO 2026-10-18 (zivi put je bio nemoguc u praksi): `write_config`
  se NIGDJE nije zvao u aplikaciji (samo u testovima) → server je dizan bez
  `opencode.json`, agent `mujofix` nije postojao, `--agent mujofix` bi pao i
  zivi put bi uvijek isao na offline. Sada `build_chain` upise config prije
  starta; radni dir je `%LOCALAPPDATA%\MujoFix\ai` (ne cwd — u EXE-u moze biti
  nezapisiv, npr. System32). MCP komanda je `mujofix.cli mcp` (nova stdio
  podkomanda; zamrznuto → `MujoFixCLI.exe mcp` jer GUI exe nema konzolu).
  Dokaz: `tests/test_mcp_stdio.py` vodi stvarni JSON-RPC handshake
  (`initialize`, `tools/list` = tačno 5 alata, sortiran katalog, `bash` =
  greska) + test da `build_chain` upise config. Ukupno 159 testa, OK.
  Otvoreno: MCP `get_findings` cita iz `--findings`/`MUJOFIX_FINDINGS`; u
  zivom toku nalazi idu u prompt, pa taj alat vraca prazno stanje — za VM
  provjeru (da li agent uopste treba taj alat).
- ISPRAVLJENO 2026-10-18 (dokazivo lokalno): `OpenCodeProvider` je zvao
  `run --format json` ("raw JSON events", dokumentovano), a plan se izvlaci iz
  ```json bloka u TEKSTU → plan se u zivom putu nikad ne bi izvukao. Sada se
  koristi default (tekstualni) izlaz; `_cmd()` izdvojen i testiran (nema
  zabranjenih flagova, nema `--format`). Dokaz o flagovima: `run --help`
  pinovanog binarnog (svi flagovi postoje); napomena — CLI ne odbija nepoznate
  flagove (kontrolni eksperiment sa `--nope` ne prijavi gresku), pa je
  `--help` jedini autoritet.
- DODANO 2026-10-18: README (bs + en) dobio sekciju "Instalacija (Windows, EXE)"
  (Setup exe preporucen, zip portabilan, provjera sha256 komandom, per-user bez
  admina, SmartScreen ocekivan, /SILENT, deinstalacija) + iskrena oznaka da
  instalater jos nije pokrenut na VM-u. README.en.md ispravljen: Zen uslovi
  "unconfirmed" → potvrdjeni, broj testova 104 → 143.
- PRIPREMLJENO 2026-10-18 (za VM korak, Issue #1/#3): `scripts/vm_validate.ps1`
  prosiren (bundlovani opencode + pin, live `update` provjera, opcioni
  `-ApplyUpdate`, nezavisna sha256 provjera setup exe-a) i `docs/TESTING.md`
  dobio F (SHA256SUMS, engleski installer) i G (auto-update + elevacija).
  netestirano: PowerShell nije dostupan u razvojnom okruzenju; logika parsiranja
  suma provjerena na stvarnom `SHA256SUMS.txt` (1 pogodak za setup exe, 64-hex).

## Faza 6 — gotova kao kod (release kapija: opciona VM lista)

- `mujofix.spec` (MujoFix.exe GUI + MujoFixCLI.exe), `installer/mujofix.iss`
  (lowest privileges, deinstalacija brise sve), `installer/OPENCODE_PIN.txt`
  (POPUNJEN: v1.18.34 + SHA-256 windows-x64; build kapija zadovoljena).
- `.github/workflows/ci.yml`: lint+testi (ubuntu+windows), build na tag sa
  SHA-256. CI prolazi zeleno; build job je vezan na `v*` tag (nije jos
  pokrenut jer tag nije kreiran).
- THIRD_PARTY_NOTICES.md (OpenCode MIT, PySide6 LGPL-3.0, Python PSF).
- docs/TESTING.md: rucna VM lista (A-F) — OPCIONA produzena validacija.
- Repo fajlovi: README.md (HTML), README.en.md, LICENSE (MIT),
  CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, CHANGELOG (0.1.0), .editorconfig,
  Issue/PR sabloni.
- Odluka: build je spreman; puna VM matrica je opciona, ne kapija.
- Auto-update (provjera GitHub Releases) implementiran kao kod:
  `mujofix/update.py` (Qt-free: `check_for_update`, `download` uz sha256,
  `apply_update`, `launch_artifact`) + `mujofix/version.py` (verzija iz
  CHANGELOG.md) + CLI `mujofix update [--apply]` + GUI dugme "Provjeri
  ažuriranja" (provjera u worker niti, preuzimanje uz sha256, pa pokretanje). Mrezni put + pokretanje preuzetog artefakta: netestirano na VM-u;
  provjera protiv pravog GitHub API-ja radi (v0.1.0 prepoznat kao najnoviji).
- `mujofix.spec`: CHANGELOG.md ide u build (runtime verzija) + `pathex=[SPEC_DIR]`
  (ranije se `mujofix.scanners` gubio u lokalnom Linux buildu jer se oslanjao na
  CWD). Validirano lokalnim PyInstaller 6.22.3 buildom: bundlovani
  `MujoFixCLI update` ispise "Verzija 0.1.0 je najnovija."
- Installer (`installer/mujofix.iss`, Inno Setup 6) se od sada kompajlira u CI
  na svakom push-u (job `installer-windows`: PyInstaller build + ISCC +
  `MujoFix-Setup-<ver>.exe` kao artefakt; verzija se cita iz CHANGELOG.md preko
  `/DMyAppVersion`). U tom job-u `dist` nema OpenCode (ne skida se pin), pa
  installer nema opencode\ — dovoljno za dokaz da se `.iss` kompajlira; pravi
  pinovani OpenCode ide u release (tag) job.
- Installer je prvi put STVARNO kompajliran (prije ovoga `.iss` nikad nije
  prosao ISCC). Popravke: `SourceDir=..` (Inno trazi `Source` relativno na
  folder `.iss`-a, pa se `dist\MujoFix\*` trazio u `installer\dist\`),
  `OutputDir=installer\Output`, i `[Languages]` uklonjen jer Inno 6.7.1 ne
  isporucuje `Bosnian.isl` (installer je na engleskom). Opencode/PIN se sada
  ubacuju u `dist` i bundluju odatle (bez dupliranja iz `build\opencode`).
- Release sada ukljucuje `MujoFix-Setup-<ver>.exe` (osim zip-a), a
  `SHA256SUMS.txt` se pise u pravom `sha256sum` formatu (`<hash>  <ime>`).
  Prije je CI pisao `Format-Table` izlaz (ljudska tabela) koji
  `update.parse_sha256sums` ne moze parsirati — verifikacija je tiho bila
  mrtva. Sada `update` preferira setup `.exe` i njegov hash se stvarno
  provjerava. (`pick_asset` bira `.exe` > `.zip`; potvrdjeno lokalno.)
- Release `v0.2.0` OBJAVLJEN (tag `v0.2.0`, build job prosao prvi put
  end-to-end): asseti `MujoFix-Setup-0.2.0.exe` (~76 MB),
  `MujoFix-v0.2.0.zip` (~115 MB), `SHA256SUMS.txt`. Provjereno protiv zivog
  release-a: `check_for_update('0.1.0')` -> dostupno, bira setup.exe, a njegov
  hash postoji u SHA256SUMS (211 unosa); `check_for_update('0.2.0')` -> nema
  update-a. Ostaje netestirano samo stvarno Windows izvrsavanje (UAC prompt +
  instalacija) — to trazi VM.
  https://github.com/xnet-ba/mujofix/releases/tag/v0.2.0
- 142/142 sa PySide6 (offscreen); Qt-free lokalno 125 uz 3 ocekivana
  import error-a (PySide6 nije instaliran). CI ubuntu + windows.

## v0.1.0-alpha.1 — PRE-RELEASE za VM testiranje (2026-10-06)

- CI potpuno zelen (ubuntu + windows testovi, 101/101).
- Realni Windows CI uhvatio 2 bug-a prije release-a: stat-bit false positive
  na Temp-u (popravljeno skip-om) i drevni PyInstaller spec format
  (prepisan na v6, validiran lokalnim buildom — bundlovani CLI radi).
- OpenCode pin: stvarni SHA-256 zvanicnog asseta (anomalyco/opencode;
  sst/org se preselio), CI skida + provjerava + bundluje.
- Release: https://github.com/xnet-ba/mujofix/releases/tag/v0.1.0-alpha.1
  (MujoFix-windows-alpha.1.zip, 49 MB, SHA gore u release notes).
  Nepotpisan, SmartScreen ocekivan, NIJE za krajnje korisnike.
- CI build sadrzi i smoke test bundlovanog exe-a (MujoFixCLI.exe scan
  na runneru PASS) — artefakt osvjezen 2026-10-06, SHA u release notes.
- Ostaje: VM validacija po docs/TESTING.md (A-F), pa tek onda v0.1.0.

## Ryzen lab (host-direct + VM u pozadini; 2026-10-13)

- SSH preko Tailscale radi (Korisnik, High integrity token); pristup snimljen
  izvan repoa. WSL2 Ubuntu-24.04, /dev/kvm OK, Docker OK.
- PREOKRET: umjesto cekanja VM-a, test direktno na host Win11 (brze, realniji
  hardver). VM ostaje za prljave testove kad zatreba.
- Host scan alpha exea (2026-10-13): 5 nalaza, 0 skipped, svih 9 scannera OK.
  Ulovljen desktop.ini bug -> popravljen + test (commit e8b0496).
  permissions-shares nalaz je iz starog builda (artefakt prije fix-a).
- GUI smoke na hostu (2026-10-14): MujoFix.exe radi stabilno u Console sesiji
  (PID 2752, 65MB, bez crasha i missing DLL); screenshot 1707x1067 sacuvan na
  laptopu (mujofix-shared/gui.png) — vizualni pregled ostaje za ljudske oci.
- Spike 1-2 PASS na hostu (2026-10-14): opencode 1.18.34 radi bez Node-a;
  serve na 127.0.0.1:45991 vraca 401 bez lozinke i 200 s lozinkom.
  Testna lozinka uklonjena iz registryja, serve task obrisan.
- Akcije 5/5 PASS na hostu pravim kodom (2026-10-14, scripts/host_proof.py):
  startup disable+rollback identican, temp clean+rollback identican,
  Spooler restart (usput ulovljen START_PENDING race -> verify sad ceka
  RUNNING do 30s + regresioni test). Restore point nije mogao (servis
  ugasen na masini) — sigurnosna mreza bili karantin manifesti + test artefakti.
- Nalazi okačeni na Issue #1 (sanirani).
- Slijed: GUI smoke na hostu -> opencode.exe (BITS) -> spike 1-2-5 rucno ->
  oprezne akcije uz odobrenje -> VM Setup kad laptop miruje.
- VM Setup 2026-10-14: ciklus detect->boot->restart je NORMALAN (Setup rebooti);
  dokaz data.img 64GB sparse + base/ver markeri, QEMU 200% CPU. NE DIRATI.

## AI-GUI spoj (2026-10-06)

- GUI dugme "Objasni nalaze (AI)": pristanak (ako nije zapamcen) ->
  anonimizacija -> FallbackChain -> tekst u log + "Sta je poslano AI-ju".
  Lanac je offline-only dok se zivi model ne nakaci uz server (Issue #1).
- `scan --out findings.json` daje payload za `mujofix_mcp.py --findings`.
- 104/104 testova prolazi.

## Repo higijena (2026-10-06)

- Pinovan PySide6==6.11.2; Dependabot (pip + actions, nedjeljno);
  gitleaks pre-commit config; secret scanning + push protection upaljeni.
- Issue-i: #1 VM validacija, #2 UAC elevator + auto-update, #3 release kapija,
  #4 Zen ToS provjera.
- Jos nije ukljucen branch protection na main-u (blokirao bi direktne push-eve
  dok zajedno iteriramo — ukljuciti kad predjemo na PR tok).

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
  duplicates (velicina->64KB->sha256; potvrdjeni visak -> karantin s rollback-om, >2GB "vjerovatno" = preporuka),
  suspicious ("sumnjivo, razlozi", potpis, Defender samo citanje),
  permissions (UAC OFF = CRITICAL, ACL, share-ovi).
- 100/100 testova prolazi. Svi Win-specficni pozivi su mockovani;
  pravi winreg/pnputil/sc/powercfg/Getty postupci cekaju VM.
- Djelimicna ziva potvrda (Win Server runner, CI artefakt windows-live-findings):
  winreg Run stavke, disk %, duplikati, startup brojac i Temp-proces rade;
  net-share parser je lazno prijavljivao header/footer — popravljen
  (cita samo tijelo) + regresioni test; novi artefakt cist.

## Faza 4 — gotova (kod + Linux dokazi, Win VM ceka)

- `ai/provider.py`: apstraktan Provider (zamjenjiv Ollama/OpenAI-kompatibilnim),
  OpenCodeProvider (`run --attach`, agent mujofix), FallbackChain (retry s
  backoff-om -> sljedeci model -> offline), kompaktni kontekst (max 10 nalaza),
  `sent_log` za ekran "sta je tacno poslano", best-effort lista modela.
- `ai/sanitize.py`: anonimizacija (ime, hostname, IP/MAC, serijski, licne putanje;
  tajni kljucevi se dropaju).
- `ai/mujofix_mcp.py`: `--findings` s pravim podacima scannera (dokazan stdio
  roundtrip), validator + cap 20 koraka + prazna akcija se odbija.
- `ui/consent.py`: ekran pristanka (kategorije + primjer STVARNOG payload-a +
  POTVRDJENI Zen uslovi besplatne razine + izvori) + SentLogViewer; default
  offline, izbor u QSettings.
- 77/77 testova prolazi.
- NIJE: tacke 3/4 spikea uz pravi model; izgled consent ekrana na Win11.
  (Zen ToS je rijesen 2026-10-18 — vidi "RIJESENO" na vrhu.)

## Faza 3 — gotova (kod + Linux offscreen dokazi, Win izgled netestiran)

- `ui/main_window.py`: jedan ekran — SCAN (worker nit), sazetak, stiklirana
  lista (sve/pojedinacno/nista), tehnicki detalji na preklopnik, POPRAVI SVE,
  progres + sigurno zaustavljanje, izvjestaj, "Ponisti sve" (rollback obrnutim
  redom). UAC akcije se izvrsavaju kad je proces admin; inace skip uz gumb
  "Pokreni kao administrator" (`windows.relaunch_elevated`, ShellExecuteW runas).
- `i18n/strings.py`: bs default + en struktura.
- `requirements.txt`: PySide6>=6.6. Testovi GUI-a: venv python +
  QT_QPA_PLATFORM=offscreen (4 testa: tok, fix+undo roundtrip, UAC skip,
  elevated se izvrsava kad je admin). Elevator netestiran na pravom UAC-u.
- 57/57 testova prolazi. Izgled na Win11 (fontovi, DPI, tamni rezim) NIJE
  vidjen — treba screenshot s VM-a.

## Faza 2 — gotova (kod + Linux dokazi, Win VM ceka)

- `actions/base.py`: Action ugovor (precondition/snapshot/apply/verify/rollback),
  Runner (pad nakon snapshot-a -> rollback), dry-run, karantin, audit log.
- 7 akcija: disable_startup_item (HKCU/HKLM, UAC samo za HKLM),
  clean_temp (starije od 7 dana u karantin, manifest), restart_service (`sc`,
  treba UAC, rizik srednji), remove_path_entry (mrtvi PATH unos, HKCU/HKLM,
  cuva registry tip), fix_temp_var (TEMP/TMP u HKCU Environment),
  disable_proxy (HKCU Internet Settings, ProxyEnable=0),
  quarantine_duplicates (potvrdjeni sha256 duplikati u karantin, jedna ostaje).
- `actions/mapping.py`: finding_to_actions izdvojen iz Qt-a (testabilno bez
  PySide6); pokriva disk-temp, disk-wu-cache, services-auto-stopped,
  startup-count, config-path-missing, config-temp-var, network-proxy,
  duplicates-found (samo `certain` grupe).
- Svaka akcija: test apply -> verify -> rollback -> stanje identicno originalu.
- 142/142 sa PySide6 (offscreen); Qt-free lokalno 125 uz 3 import error-a.

## Faza 1 — gotovo (kod + Linux dokazi, Win VM ceka)

- `core/models.py`: Finding (obavezan evidence, CRITICAL/MEDIUM/LOW) + ScanReport.
- `platform/windows.py`: verzija/build detekcija, winreg wrapperi (stdlib).
- `scanners/base.py`: interfejs, ScanContext(cancel), registry; greska = skipped.
- Scanneri: startup (Run/RunOnce + Startup folderi), disk (prostor + temp +
  WU kes + Windows.old), services (Get-Service auto/stopped).
- `cli.py`: `scan` (JSON) + `--summary` (obican jezik).
- 34/34 testova prolazi; zivi `scan --summary` na Linuxu radi
  (disk nadje, startup/services se graceful preskoce).
