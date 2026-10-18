# Changelog (semantičko verzioniranje; `mujofix.spec` čita vrh ovog fajla)

## [Unreleased]
### Dodano
- Zivi put je sada stvarno upotrebljiv: `build_chain` prije starta servera
  upise izolirani `opencode.json` (bez toga server nema agenta `mujofix` ni MCP
  alate, pa bi `run --agent mujofix` pao). Config ide u
  `%LOCALAPPDATA%\MujoFix\ai` (ne u cwd, koji u EXE-u moze biti nezapisiv).
  MCP komanda: `mujofix.cli mcp` (novi stdio mod; zamrznut → `MujoFixCLI.exe`
  `mcp`, jer GUI exe nema konzolu). Novi `tests/test_mcp_stdio.py` dokazuje
  stvarni MCP handshake: `initialize`, tačno 5 alata, sortirani katalog,
  nepoznat alat = greska.
- Zivi AI put u GUI-ju: uz pristanak se u pozadinskoj niti (`ExplainWorker`)
  digne ugrađeni `opencode serve` (127.0.0.1, slucajna lozinka) i koristi
  besplatan Zen model; bez pristanka ili na svaki kvar (nema binary-ja, server
  se ne digne, nema besplatnog modela) lanac ostaje **offline** uz iskren
  razlog. `build_chain`/`LiveSession` drze vlasnistvo nad procesom i gase ga
  na zatvaranju prozora (bez zaostalih procesa). netestirano na Windows VM-u.
### Ispravljeno
- AI plan se nije prikazivao (validirao se pa bacao): sada se prikaze kao
  citljiva lista koraka; primjena i dalje ide preko akcija odabranih nalaza.
- Zivi put: prompt je tvrdio da nalazi dolaze samo kao MCP podaci (a u zivom
  putu `get_findings` je prazan) i `get_system_info` je bez snimka vracao
  lazni "spike" fixture modelu koji ne smije izmisljati. Prompt sada opisuje
  stvarni put (nalazi = podaci u poruci), prazan snimak daje postenu biljesku.
- Ekran pristanka prikazuje tacan tekst zahtjeva (i onaj koji stvarno ide
  modelu): ista funkcija `build_prompt` gradi i primjer i zahtjev.
- Privatnost: anonimizacija se prije radila SAMO za ekran "sto je poslano",
  a modelu su isli sirovi nalazi (`C:\Users\<ime>\...`, IP, MAC, serijski).
  Sada `FallbackChain.explain` anonimizira jednom na ulazu — poslano i
  logovano su isti payload.
- `ai/agent_config.py`: agent je bio `mode: "subagent"`, a `opencode run
  --agent mujofix` tada tiho koristi DEFAULT agent (sa svim alatima) —
  zabrana alata se zaobilazila. Sada `mode: "all"`; dokazano protiv pinovanog
  binarnog (upozorenje "Falling back to default agent" samo za subagent).
- `ai/agent_config.py`: config je bio V2 oblik koji pinovani (V1) opencode
  odbija (`ConfigInvalidError`, 400) — zivi put bi pao pri startu. Sada V1
  (`mcp` mapa, `agent`, `prompt`, `tools`: svi ugradjeni alati `false`,
  `mcp_*: true`); imena alata iz pinovanog `agent create --help`. Novi
  integracioni test to dokazuje protiv stvarnog binarnog (200 + deny).
- `ai/provider.py`: `run --format json` daje event stream, a plan se cita iz
  ```json bloka u tekstu — plan se nikad ne bi izvukao. Vraceno na default
  (tekstualni) izlaz; `_cmd()` izdvojen i pokriven testom.
- `free_zen_models` je vracao prazno (filtrirao po "zen", stvarni ID-jevi su
  `opencode/<id>`); sada prepoznaje besplatne Zen modele po stvarnom prefiksu
  `opencode/` + "-free" marker (+ lista stealth modela), a potencijalno placene
  ne ukljucuje.
### Promijenjeno
- Pristanak (consent) i README: uslovi OpenCode Zen besplatne razine su
  potvrđeni iz primarnih izvora (ToS + Zen docs, 2026-10-18) — umjesto
  "NEPOTVRĐENI" stoji konkretna tvrdnja (neplaćeni računi: sadržaj se smije
  koristiti za unapređenje usluge; pojedini besplatni modeli mogu koristiti
  podatke za poboljšanje modela; dio zahtjeva se čuva 30 dana). Dodat test
  koji čuva to stanje.

## [0.2.0] - 2026-10-18
### Dodano
- Auto-fix: `quarantine_duplicates` (potvrđeni sha256 duplikati u karantin, jedna kopija ostaje).
- Elevacija: gumb "Pokreni kao administrator" + izvršavanje `needs_elevation`
  akcija kad je proces admin (`windows.is_admin`/`relaunch_elevated`).
- Auto-update: provjera GitHub Releases (`mujofix update`), preuzimanje
  uz sha256 verifikaciju (`mujofix update --apply`); `mujofix/update.py`,
  `mujofix/version.py`, GUI dugme "Provjeri ažuriranja".
- CI kompajlira Inno Setup installer na svakom push-u (job
  `installer-windows`, artefakt `MujoFix-Setup-<ver>.exe`).

### Ispravke

- `SHA256SUMS.txt` u release-u je sada u `sha256sum` formatu (`<hash>  <ime>`).
  Prije je nastajao iz `Format-Table` (ljudska tabela), pa
  `update.parse_sha256sums` nije mogao naci hash — verifikacija preuzetog
  fajla je tiho bila preskocena.
- `installer/mujofix.iss`: `SourceDir=..` (Source putanje su relativne na repo
  root), `OutputDir=installer\Output`, bez `[Languages]` (Inno 6.7.1 ne
  isporucuje `Bosnian.isl`). Prvi put stvarno kompajliran.
- Release sada prilaze `MujoFix-Setup-<ver>.exe` (koji `update` preferira nad
  `.zip`).
### Napomene
- Elevator (pravi UAC prompt) i Win izgled ostaju netestirani na VM-u.
- Auto-update mrežni put i pokretanje preuzetog artefakta: netestirano na VM-u.

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
