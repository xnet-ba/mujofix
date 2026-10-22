# Changelog (semantičko verzioniranje; `mujofix.spec` čita vrh ovog fajla)

## [0.4.0] (u razvoju — nije objavljeno)

### Ispravljeno
- **`load_findings_file` sada odbija neispravan snapshot odmah** (mora biti
  objekat sa `findings` **listom objekata**), umjesto da greška ispliva
  duboko kasnije u obradi alata.
- **MCP server je mogao umrijeti od neispravne poruke:** `serve()` je čitao
  `msg.get(...)` **izvan** `try` bloka, pa je validan JSON koji nije objekat
  (npr. `[1,2]`) bacao `AttributeError` i **ubijao server** — a poruke dolaze
  od vanjskog procesa (opencode/model). Unutar `try` se hvatao samo
  `ValueError`, pa je i `params` koji nije objekat rušio server. Sada je
  obrada izdvojena u `handle_message()` koja **nikad ne baca** (vraća
  JSON-RPC grešku), uz provjere tipova; mrtve `_respond`/`_respond_error`
  su uklonjene. Testovi: fuzz kroz `handle_message` + pravi stdio test koji
  prvo pošalje 6 linija smeća pa traži normalan odgovor.
- **Update granica očvrsnuta protiv neispravnih podataka s mreže:**
  `find_asset`/`pick_asset` su radili `asset["name"]` → **`KeyError`** (ne
  `UpdateError`) na unosu bez imena, a CLI hvata samo `UpdateError` — pa bi
  pukao; `release.get("assets", [])` je vraćao `None` kad ključ postoji sa
  `None` → `TypeError`; `fetch_latest` nije provjeravao da je odgovor JSON
  **objekat**. Sada: neispravni unosi se preskaču, odgovor mora biti
  objekat (`up_bad_response`), a `pick_asset` nikad ne bira `SHA256SUMS` i
  uvijek traži `.exe`/`.msi`/`.zip` sa URL-om. Provjereno i protiv stvarnog
  release-a (legitiman put i dalje bira `MujoFix-Setup-0.3.0.exe`).
- **Update je tiho preskakao verifikaciju hash-a** (sigurnosna rupa): ako je
  `SHA256SUMS.txt` postojao ali se nije mogao pročitati ili u njemu nije bilo
  našeg fajla, kod je postavljao `expected = None` i **preuzimao i pokretao
  neprovjeren fajl** — suprotno onome što `docs/TESTING.md` tvrdi. Sada je
  fail-closed: nema `SHA256SUMS`-a, ne može se pročitati, ili nema unosa za
  naš fajl → `UpdateError`, ništa se ne preuzima. Provjereno i protiv
  stvarnog release-a (v0.3.0 ima hash za `MujoFix-Setup-0.3.0.exe`, pa
  legitiman put i dalje prolazi).
- **Fuzz testovi su našli tri slabljenja na granicama** (validator AI plana i
  anonimizacija) i sva tri su popravljena: (1) token koji se pojavi u
  VRIJEDNOSTI (npr. u slobodnom tekstu nalaza) nije se skidao — sada se
  skidaju poznati oblici (`ghp_`/`gho_`/`ghu_`/`ghs_`/`github_pat_`, `sk-`,
  `xox[baprs]-`, `AKIA…`, `Bearer …`); (2) validator je prihvatao metu koja
  je samo razmaci; (3) prihvatao je i besmislenu metu ("0") i višelinijski
  tekst — sada meta mora imati slovo, bez kontrolnih znakova, ≤ 260 znakova.
  Anonimizacija serijskih brojeva pokriva i mala slova, ali uz uslov da
  sadrže cifru (da ne pojede običan tekst tipa "windows-update").
  Ekran pristanka (bs+en) to sada i kaže.

### Dodano
- **Sažetak kaže koliko se problema može automatski popraviti** (pored broja
  po ozbiljnosti); ako nijedan nalaz nema akciju, to izričito kaže i upućuje
  na preporuke. Snimke u README-u regenerisane.
- **Nova akcija `remove_share`:** nalaz `permissions-shares` nije imao
  popravku. Snapshot pamti putanju i remark (`net share <ime>`), apply je
  `/delete`, verify traži da share nema, rollback ga vraća. Administrativni
  share-ovi (`C$`, `ADMIN$`, `IPC$`, `print$`…) se nikad ne diraju (ista
  `DEFAULT_SHARES` lista kao u scanneru); traži elevaciju.
- **Nova akcija `disable_power_saver`:** nalaz `config-power-saver` nije
  imao popravku. Snapshot pamti GUID aktivnog plana, apply prebacuje na
  Balanced (`powercfg /setactive`), verify traži da je Balanced aktivan, a
  rollback vraća stari GUID. Ne traži elevaciju; ako apply padne, stanje se
  vraća bez lažne tvrdnje o uspjehu. GUID za Balanced je iz primarnog
  izvora (Microsoft powercfg docs, provjereno 2026-10-22) i test to čuva.
- **Nova akcija `remove_hosts_entry`:** nalaz `network-hosts` (sumnjiv
  zapis u hosts fajlu = DNS hijack) do sada nije imao popravku. Snapshot
  čuva cijeli hosts fajl, uklanja se tačno prijavljeni zapis, ostatak
  ostaje netaknut, upis je atomaran, verify traži nestanak zapisa uz
  identičan ostatak, a rollback vraća bajt-identično. Traži elevaciju
  (hosts je zaštićen); nije u AI allowlisti — ide kroz odabrane nalaze.
- **Dovršena lokalizacija akcija i CLI-ja:** poruke akcija (precondition/
  apply/verify/rollback + greške) idu kroz `ctx.t(...)` (jezik u
  `ActionContext`), opis i rizik akcije preko `action_text(...)` (klasni
  atributi ne mogu zvati `self`), nazivi koraka AI plana i razlozi
  validacije (`validate_plan(plan, lang)`), greške update-a i CLI izlaz
  (`update --lang`). Čuvar `tests/test_action_i18n.py` (ratchet: nema
  hardkodovanih poruka; svaka akcija ima bs+en opis i rizik, i to različit).
  Usput popravljeno: MCP pokrenut **po putanji** (`python mujofix/ai/
  mujofix_mcp.py`) nije mogao `import mujofix` (novi i18n import) — sada
  dodaje korijen repoa na `sys.path`.
- **Dvojezični nalazi (bs/en), svi skeneri:** engleski UI je prikazivao
  bosanski sadržaj nalaza. Sada tekst nalaza nastaje na jeziku konteksta
  (`ScanContext.lang` + `Scanner.t()`), pa su naslov/zašto/uticaj/rizik,
  „skipped" razlozi, offline objašnjenja i CLI izlaz (`scan --lang
  bs|en`) na jednom jeziku. Čuvar `tests/test_scanner_i18n.py` provjerava
  da sva polja idu kroz `self.t(...)` (ratchet lista — dijakritike same
  nisu dovoljan signal jer je mnogo bosanskog teksta ASCII).
- **Bogatija offline objašnjenja** (put koji većina korisnika vidi, jer
  besplatni Zen tier odbija poziv iz našeg CLI-a): umjesto jednog reda,
  objašnjenje sada nosi zašto/uticaj/rizik (i da li se može poništiti)/
  dokaz/tehničke detalje + šta aplikacija može (postoji li akcija u
  katalogu). Gradi se ISKLJUČIVO iz podataka nalaza — polja koje nema se
  izostavljaju, ništa se ne popunjava pretpostavkom. Dvojezično (bs/en),
  uključujući „note" linije lanca.
- **Pregled karantina:** lista šta je unutra (datum, veličina, originalna
  putanja) i vraćanje pojedinačnih fajlova — uključujući one iz RANIJIH
  sesija; do sada je poslije restarta preostajalo samo trajno brisanje
  („Poništi sve" zna samo za tekuću sesiju). Fajl bez manifesta nema
  poznatu originalnu putanju, pa se može samo obrisati (i to se kaže).
- **Čišćenje karantina + stvarno „oslobođeno":** karantin se prije NIKAD nije
  čistio (fajlovi su ostajali u `%LOCALAPPDATA%\MujoFix\quarantine`), pa
  tvrdnja o oslobođenom prostoru nije bila istinita. Novi
  `quarantine_usage()`/`purge_quarantine()` u `actions/base.py`, zapis u
  karantinu pamti veličinu fajla PRIJE premještanja, a GUI ima dugme
  „Očisti karantin" koje pokaže broj fajlova i GB, traži potvrdu i u izvještaj
  upiše oslobođeno. Dugme „Poništi sve" i dalje vraća fajlove iz karantina.
- Izvještaj sada pokazuje i koliko je trenutno u karantinu.
- Testovi: `tests/test_quarantine.py` (4) + GUI (potvrda, otkazivanje,
  brojke); README (bs+en) ažuriran.

### Ispravljeno
- **Windows konzola je pukla na dijakriticima** (`UnicodeEncodeError`):
  uvođenjem dvojezičnog teksta nalaza i sažetka (`računar`, `keš`)
  `MujoFixCLI.exe` je pao u CI smoke koraku na legacy code page. Sada se
  stdout/stderr prebacuju na UTF-8 (`errors="replace"`), pa se ne može
  srušiti ni na terminalu bez podrške za znak. Smoke korak sada vrti
  `scan --lang en --summary` (stabilan izlaz + testira `--lang` na Win).

## [0.3.0] - 2026-10-21

### Promijenjeno
- **Uklonjen lokalni backend:** MujoFix je isključivo instalabilna Windows
  aplikacija — nema `opencode serve`, porta ni lozinke, ništa se ne izlaže na
  mreži. Živi model ide kroz `opencode run` kao child proces (jedan po
  zahtjevu). Uklonjeni su `OpencodeServer`, `pick_free_port`, health-check i
  vlasništvo nad procesom; `LiveSession` sada samo nosi stanje
  (`chain`/`note`/`live`). `FORBIDDEN_FLAGS` zabranjuje i
  `--attach`/`--port`/`--hostname` (čuvari da se server ne vrati).
- **Izgled: Fluent 2 / Windows 11** — Segoe UI, zaobljene kontrole, automatska
  svijetla/tamna tema (`AppsUseLightTheme`, override `MUJOFIX_THEME`), Mica
  pozadina na Win11 preko DWM (best-effort: ako poziv ne uspije, ostaje solidna
  boja), ikona aplikacije u exe-u/installeru/prozoru i snimke u README-u.
- Pristanak (consent) i README: uslovi OpenCode Zen besplatne razine potvrđeni
  iz primarnih izvora (ToS + Zen docs, 2026-10-18) — neplaćeni računi: sadržaj
  se smije koristiti za unapređenje usluge; pojedini besplatni modeli mogu
  koristiti podatke za poboljšanje modela; dio zahtjeva (OpenAI/Anthropic) čuva
  se 30 dana. Test čuva to stanje.

### Dodano
- **JSON dnevnik izvršavanja** (sve faze koraka + sažetak) u
  `%LOCALAPPDATA%\MujoFix\audit\` poslije svake popravke; putanja ide u log, a
  kvar dnevnika ne ruši aplikaciju. Novi `mujofix/audit.py` + `tests/test_audit.py`.
- **Probni (dry-run) mod** u GUI-ju (checkbox): prolazi precondition i prikaže
  šta bi uradio, a ništa ne mijenja; report to izričito kaže i dnevnik se
  označava kao `dry-run`.
- **Izbor jezika (Bosanski/English)** u UI-ju (primjenjuje se pri sljedećem
  pokretanju) i pamćenje veličine/pozicije prozora.
- **Dugme „AI: uključi/isključi"**: pristanak se može promijeniti bilo kad
  (prije se ekran prikazivao samo jednom, pa je obećanje „isključi bilo kad"
  bilo netačno).
- **UI je kompletno dvojezičan** (bs+en) i pokriven `tests/test_i18n.py`
  (paritet ključeva, nema hardkodovanog teksta u `mujofix/ui/`).
- **`mujofix.cli mcp`** — stdio MCP server (zamrznuto `MujoFixCLI.exe mcp`);
  `tests/test_mcp_stdio.py` dokazuje stvarni handshake: `initialize`, tačno 5
  alata, sortiran katalog, nepoznat alat = greška.
- **Testovi/cuvari:** `tests/test_theme.py`, `tests/test_icon.py`,
  `tests/test_workflows.py` (hvata YAML trap koji tiho ugasi CI),
  `scripts/make_icon.py`, `scripts/make_screenshots.py`.
- **CI:** smoke korak u `installer-windows` na svakom push-u — zapakovani
  `MujoFixCLI.exe` mora proći `scan --summary` i `update`.

### Ispravljeno
- **Anonimizacija je štitila samo ekran, ne i zahtjev:** model je dobijao
  sirove nalaze (`C:\Users\<ime>\...`, IP, MAC, serijski), a ekran „šta je
  poslano" je prikazivao očišćenu kopiju. Sada `FallbackChain.explain`
  anonimizira jednom na ulazu — poslano i logovano su isti payload.
- **Ekran pristanka je prikazivao drugi tekst** od onoga što stvarno ide
  modelu; sada ista funkcija (`build_prompt`) gradi i primjer i zahtjev.
- **Agent je bio `mode: "subagent"`** → `opencode run --agent mujofix` je tiho
  koristio DEFAULT agent (sa svim alatima), pa se zabrana alata zaobilazila.
  Sada `mode: "all"`; dokazano protiv pinovanog binarnog.
- **Config je bio V2 oblik** koji pinovani (V1) opencode odbija
  (`ConfigInvalidError`) — živi put bi pao. Sada V1 (`mcp` mapa, `agent`,
  `prompt`, `tools`: svi ugrađeni alati `false`, `mcp_*: true`); dokaz:
  `opencode debug config` sa izolovanim config-home (agent + `deny`, samo naš
  MCP, 0 pluginova).
- **Config se nikad nije upisivao u aplikaciji** (samo u testovima), pa agent
  `mujofix` nije ni postojao u živom putu — sada `build_chain` upisuje izolirani
  `opencode.json` u `%LOCALAPPDATA%\MujoFix\ai` (ne u cwd, koji u EXE-u može
  biti nezapisiv).
- **„Izolovani" config se stvarno stucao sa korisničkim globalnim**
  (`~/.config/opencode`): agent je naslijedio tuđe MCP servere (npr. playwright)
  i pluginove. Sada child dobija `XDG_CONFIG_HOME`; kredencijali (`auth.json`)
  ostaju u data diru.
- **Prompt je tvrdio da nalazi dolaze samo kao MCP podaci**, a u živom putu
  `get_findings` je prazan; `get_system_info` je bez snimka vraćao lažni
  „spike" fixture modelu koji ne smije izmišljati. Prompt sada opisuje stvarni
  put (nalazi = podaci u poruci), a prazan snimak daje poštenu bilješku.
- **AI plan se validirao pa bacao** — korisnik ga nikad nije vidio; sada se
  prikaže kao čitljiva lista koraka (primjena i dalje ide preko akcija
  odabranih nalaza).
- **`run --format json` daje event stream**, a plan se čita iz ```json bloka u
  tekstu — plan se nikad ne bi izvukao. Vraćeno na tekstualni izlaz.
- **`free_zen_models` je vraćao prazno** (filtrirao po „zen", stvarni ID-jevi
  su `opencode/<id>`); sada prepoznaje besplatne Zen modele po prefiksu
  `opencode/` + `-free` marker (i lista stealth modela), a potencijalno plaćene
  ne uključuje.
- **Engleski UI je curio bosanski** (hardkodovan tekst van `tr()`): naslov i
  dugmad ekrana pristanka, naslov pregleda poslanog i log poruke; sada sve ide
  kroz `tr()` uz čuvar u testovima.
- **Installer je pao u CI** jer Inno rješava `SetupIconFile` relativno na
  `SourceDir` (repo root), a ne na folder `.iss`-a; popravljeno i pokriveno
  testom koji rješava putanje kao Inno.
- **README je obećavao više od koda:** „paralelni moduli skeniranja" (svi se
  izvršavaju redom), modul „Performanse" sa „boot vremenom" (ne postoji),
  „5/5 akcija" (katalog ima 7; host dokaz pokriva 3), „izvještaj prije/poslije"
  i „export registry ključeva"/„System Restore Point" (nije implementirano),
  `143` testa (sada 211). Sve ispravljeno u bs+en.
- **Crna lista zaštićenih zona je bila uža od tvrdnje i preširoka odjednom:**
  dodane su Program Files, Dokumenti/Slike/Desktop/Download, boot BCD i
  Defender, a uklonjen `c:\windows` jer je blokirao i legitiman
  `C:\Windows\Temp` i WU cache.

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
