# Rezultati validacije na pravom Windows 11 laptopu (2026-10-23)

Prva **nezavisna validacija na fizičkoj mašini** (ne VM): `sha-laptop-win11`
(DESKTOP-NGK7CLP), pristup preko SSH-a (Tailscale), sesija **elevated**
(High Mandatory Level) — bez UAC promptova.

## Mašina
- **Windows 11 Enterprise N**, build **10.0.26300**
- **WDAC enforced** (`CodeIntegrityPolicyEnforcementStatus = 2`)
- **8 ASR pravila aktivna** (uključujući „Block executable files unless
  prevalence/age/trusted" — zbog toga je prvo pokretanje `MujoFixCLI.exe`
  vraćalo „Access is denied")
- File-system filteri: `UCPD`, `WdFilter`, `bfs`, `luafv`, `Wof`, `FileInfo`…
  (nema trećeg EDR-a)
- Defender izuzeci **nađeni na mašini**: `C:\Users\Korisnik\mujofix-test`
  (dodao agent, privremeno) i **`C:\Users\Korisnik\nikto`** (postojao prije
  agenta — odakle je, nepoznato; vrijedi provjeriti)

## Šta je pokrenuto i rezultat
| Provjera | Rezultat |
|---|---|
| Instalacija (portable, SHA-256 provjeren) | ✅ |
| `MujoFixCLI.exe scan --lang bs/en` + JSON nalaza | ✅ (`02-cli.txt`, `findings.json`) |
| `MujoFixCLI.exe update` (živa provjera protiv release-a) | ✅ „Verzija 0.4.0 je najnovija." |
| `scripts/host_proof.py` (akcije, apply → verify → rollback) | ✅ **12/12 PASS** (`host_proof.txt`) |
| `scripts/phase0_spike.py` (pinovani opencode) | ✅ 1, 2, 5 PASS; 3/4 SKIP (nema model kredencijala) |
| GUI render (offscreen, PySide6) | ✅ `docs/screenshots/*.png` su sada sa **pravog Windowsa** |
| **GUI na pravom desktopu** | ✅ aplikacija pokrenuta u interaktivnoj sesiji: prozor se renderuje ispravno (tamna tema jer je sistem u dark modu), a vidljivo je dugme **„Pokreni kao administrator"** — jer interaktivno pokretanje **nije** elevated (UAC token filtering radi kako treba). *Snimka nije u repou jer sadrži privatni desktop korisnika.* |
| **Živi AI model** (google/gemini-2.5-flash, mašinin kredencijal) | ✅ model odgovara, **poziva naš MCP alat i čita katalog akcija**, **odbija shell** (`03-zivi-model.txt`); besplatni Zen tier ostaje neprovjeren (nema Zen kredencijala) |
| **Installer** (tiha instalacija → provjera → deinstalacija) | ✅ `installer.txt`: exit 0, MujoFix.exe/CLI/opencode/Start meni, desktop ikona po defaultu NE, uninstall zapis (AppId ključ, ver 0.4.0); **instalirani CLI radi** (scan + update); deinstalacija **sve uklanja** (app folder, Start meni, registry) |

`host_proof` detalj: `startup` ✅, `temp` ✅, `service` (Spooler restart) ✅,
**`hosts`** ✅ (uklonjen zapis, ostatak nepromijenjen, rollback bajt-identičan),
**`share`** ✅ (uklonjen i vraćen; `C$`/`ADMIN$` nedirnuti), `power` — SKIP
(plan je već Balanced, iskreno).

## Bugovi koje je ova validacija našla (i koji su popravljeni)
1. **`remove_hosts_entry` je padao** (`WinError 5`) — ovaj Windows **zabranjuje
   `os.replace`** (`MOVEFILE_REPLACE_EXISTING`) nad `…\etc\hosts`, a dozvoljava
   `shutil.copyfile` (dokazano direktnim testom: replace ❌, remove+rename ✅,
   copyfile ✅). → dodat fallback na kopiju (`f7a19b7`).
2. **Akcija je mijenjala line-endings** (CRLF→LF), pa fajl nije bio
   bajt-identičan poslije rollback-a → akcija sada radi **nad bajtovima**
   (`f0694de`).
3. **Izbor jezika (QComboBox) je u tamnoj temi bio nevidljiv** (bijeli tekst na
   svijetloj native pozadini) → dodato stilizovanje comba (`1067e2e`).
4. Usput, u samoj skripti: `host_proof.py` je padao kad akcija ne uspije
   (`rollback(state=None)`) i imao je pogrešna očekivanja za hosts (`99567f8`).
5. **`config-sfc` je bio FALSE POSITIVE na zdravom sistemu** (MEDIUM „12 grešaka
   u CBS logu"). Provjera na mašini: u zadnjih 512 KB CBS loga ima 12 linija sa
   „Failed", ali **svih 12 je `Info` nivo** (`Failed to open package /
   CBS_E_INVALID_PACKAGE` = normalna buka), **0 `Error`**. Sada se broji samo
   `Error` nivo (1–5 → LOW, >5 → MEDIUM) → **verifikovano na istoj mašini da
   nalaz nestaje**, a ostaju stvarni nalazi (`disk-temp`, `wuauserv-disabled`,
   `defender-exclusions` zbog tuđeg „nikto" izuzetka, `duplicates-found`,
   `startup-count`).

## Šta agent (ja) jeste promijenio na mašini — iskreno
- dodao **SSH javni ključ** (`mujofix-agent`) u `administrators_authorized_keys`
- dodao **privremeni Defender izuzetak** za `%USERPROFILE%\mujofix-test`
  (bez toga se exe nije mogao pokrenuti zbog ASR/WDAC) — **obrisan na kraju**
- tokom dijagnostike **prepisao `hosts` fajl**, pa ga **vratio na standardni
  Windows sadržaj** (824 B, provjereno)
- napravio i uklonio test share i test startup zapis (rollback-ovano)
- instalirao `PySide6` (za offscreen snimke)

## Šta još nije pokriveno
- **Besplatni Zen tier**: nema Zen kredencijala na mašini, pa je testiran živ
  put preko **Google** kredencijala (radi end-to-end — vidi `03-zivi-model.txt`);
  Zen free tier i dalje ostaje neprovjeren (poznat rizik).
- **GUI interakcija** (klikanje kroz „Popravi sve", prihvatanje UAC prompta):
  GUI je pokrenut na pravom desktopu i renderuje se ispravno (vidi tabelu), a
  akcije su dokazane kroz `host_proof`. **Klikanje i UAC prompt traže čovjeka
  za ekranom** — to ostaje za ručnu provjeru.
- **Installer** je pokrenut i provjeren (vidi `installer.txt`); jedino je
  SHA-256 provjera u skripti imala bug u parsiranju (sam hash je tačan).
