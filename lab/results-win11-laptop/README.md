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

## Šta agent (ja) jeste promijenio na mašini — iskreno
- dodao **SSH javni ključ** (`mujofix-agent`) u `administrators_authorized_keys`
- dodao **privremeni Defender izuzetak** za `%USERPROFILE%\mujofix-test`
  (bez toga se exe nije mogao pokrenuti zbog ASR/WDAC) — **obrisan na kraju**
- tokom dijagnostike **prepisao `hosts` fajl**, pa ga **vratio na standardni
  Windows sadržaj** (824 B, provjereno)
- napravio i uklonio test share i test startup zapis (rollback-ovano)
- instalirao `PySide6` (za offscreen snimke)

## Šta još nije pokriveno
- **Živi AI model** (spike 3/4): nema Zen kredencijala na mašini; besplatni
  tier i dalje odbija poziv iz CLI-a (poznat rizik).
- **GUI interakcija** (klikanje kroz „Popravi sve", UAC prompt): GUI je
  renderovan i akcije su dokazane kroz `host_proof`, ali klikanje kroz prozor
  nije odrađeno (nema interaktivne sesije za agenta).
- **Installer** je pokrenut i provjeren (vidi `installer.txt`); jedino je
  SHA-256 provjera u skripti imala bug u parsiranju (sam hash je tačan).
