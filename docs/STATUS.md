# STATUS.md — stanje projekta (azurirano: 2026-10-21)

## Aplikacija zavrsena (kod + host dokazi; 2026-10-17)

- Faze 0-6 su kompletne u kodu. Nema TODO/FIXME/stub-ova u `mujofix/`.
- Potvrdjeno host-direct na pravom Windows 11 (laptop, High integrity token):
  scan 9/9 scannera / 0 skipped, GUI smoke, spike 1-2 (opencode 1.18.34 bez
  Node-a, tada `opencode serve` na 127.0.0.1 + lozinka). Detalji nize u
  "Ryzen lab".
  NAPOMENA 2026-10-21: server je uklonjen (`opencode run` je child proces —
  vidi unos ARHITEKTURA); katalog danas ima 8 akcija, a `scripts/host_proof.py`
  pokriva 3 (startup, temp, servis) — ostale kroz testove.
- 104/104 unit testa u tom runu; trenutno 193 lokalno (Linux/offscreen).
- Integracioni testovi protiv binarnog: config dokazan na 1.18.34, novi put
  `opencode run` bez servera na 1.18.35 (host instalacija); pin za bundle
  ostaje 1.18.34 (`installer/OPENCODE_PIN.txt`).
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
  (bash/edit/webfetch/websearch/task), preskace se bez binarnog.
  [NADGLASANO 2026-10-21: `opencode serve` je uklonjen; isti dokaz sada ide
  preko `opencode debug config` — vidi unos ARHITEKTURA.] Zasto je
  `mcp_*` izricito `true`: globalni default je `ask`, a neinteraktivni `run`
  ne moze dobiti odobrenje. Ukupno 153 testa, OK.
- IMPLEMENTIRANO 2026-10-18 (zivi AI put, Issue #1 ostatak): `ExplainWorker`
  (QThread) gradi lanac van GUI niti; `build_chain`/`LiveSession` u
  `ai/provider.py` dizu `opencode serve` samo uz pristanak i gase ga na
  zatvaranju prozora (`closeEvent` + `close()` pri novom objasnjenju).
  [NADGLASANO 2026-10-21: nema servera ni vlasnistva nad procesom; ziv poziv je
  `opencode run` child, a `LiveSession` nosi samo stanje.]
  Svaki kvar (nema binary-ja, server, besplatni model) → offline lanac + iskren
  razlog u logu. Testovi: 6 novih (5 Qt-free u test_faza4a, 1 GUI lifecycle u
  test_faza4c); ukupno 149 (+2 za V1 config +2 za _cmd = 153). netestirano: zivi put nije
  pokrenut na Windows VM-u (nema UAC/VM okruzenja, ne trosi se mreza).
- ISPRAVLJENO 2026-10-18 (README je obećavao mjerenje koje ne postoji):
  "IZVJEŠTAJ — prije/poslije (oslobođeni GB, vrijeme boot-a, broj startup
  stavki)" — stvarno se prikazuje samo broj popravljenih/preskocenih/neuspjelih
  + "Poništi sve". Boot vrijeme se ne mjeri nigdje (to izricito kaze i
  `scanners/startup.py`). README (bs+en) sada opisuje stvarno stanje.
- DOKAZ 2026-10-21 (ziv put, bez servera): `opencode run --agent mujofix --dir
  <wd> --model opencode/beam-free ping` prolazi kroz pinovani binarni bez
  `--attach` i bez servera (nema greske o nepoznatom flagu), ali vrati:
  "Error: OpenCode's free tier can only be used from within OpenCode." rc=1.
  Znaci: besplatni Zen tier se odbija iz naseg child poziva na ovoj masini
  (jedini kredencijal je OpenRouter). Provider to pretvara u ProviderError ->
  iskren offline fallback sa razlogom. RIZIK za zivi put: besplatni tier mozda
  nije upotrebljiv iz bundlovanog CLI-a — potvrditi na VM-u sa Zen nalogom
  (Issue #1). Ovo NIJE greska flagova: komanda je prihvacena.
- ARHITEKTURA 2026-10-21 (uklonjen lokalni backend): app je SAMO instalabilna
  Windows aplikacija — nema `opencode serve`, nema HTTP porta ni lozinke, nista
  se ne izlaze na mrezu. Ziv poziv je `opencode run` kao child proces (jedan po
  zahtjevu). Uklonjeno: `OpencodeServer`, `pick_free_port`,
  `OpencodeNotHealthy`, health-check, `urllib`/`base64`/`secrets`; `LiveSession`
  vise nije vlasnik procesa (nosi samo `chain`/`note`/`live`). `FORBIDDEN_FLAGS`
  sada zabranjuje i `--attach`/`--port`/`--hostname`. Novi
  `agent_config.child_env(workdir)` daje child-u `XDG_CONFIG_HOME` (+ PYTHONPATH
  u dev-u). Dokaz bez servera i bez modela: `opencode debug config` sa
  izolovanim config-home pokaze nas agent, 11 alata `deny`, samo nas MCP, 0
  pluginova (testovi u `test_phase0_spike.py`); spike CHECK 2 je prepisan na to.
- AKCIJA 2026-10-22 (nova popravka): nalaz `network-hosts` (DNS hijack zapis u
  hosts fajlu) je do sada bio SAMO preporuka — nije imao akciju. Sada
  `mujofix/actions/hosts.py` (`remove_hosts_entry`): snapshot cuva CIJELI hosts
  fajl, uklanja se tacno prijavljeni zapis (ip+ime), ostalo (komentari, drugi
  zapisi) ostaje netaknuto, upis je atomaran (temp + os.replace), verify trazi
  da je zapis nestao i da je ostatak identican, rollback vraca bajt-identicno.
  `needs_elevation=True` (hosts je zastita na Windowsu) — bez admina se preskace
  kroz postojeci UAC obrazac. Namjerno NIJE u `ACTION_ALLOWLIST` (AI ne smije
  predlagati izmjenu hosts fajla; ide samo kroz odabrane nalaze). Testovi:
  `tests/test_hosts_action.py` (8) — apply/verify/rollback identicno, cuvanje
  ostatka fajla, odbijanje kad zapisa nema, dvojezicne poruke, mapping.
- I18N-AKCIJE 2026-10-22: ista lokalizacija za akcije i CLI. `ActionContext.lang`
  + `ctx.t(...)` za poruke (Runner i svih 7 akcija), `action_text(action, field,
  lang)` za `description`/`risk` (klasni atributi ne mogu zvati self), `plan_lines
  (plan, lang)` + `ACTION_LABELS` za bs/en, `validate_plan(plan, lang)` za razloge,
  `update.py` poruke + `update --lang`, GUI `UpdateWorker(lang)`. Cuvar
  `tests/test_action_i18n.py` (ratchet + render testovi + EN bez dijakritika).
  NAPOMENA (iskreno): tehničke poruke izuzetaka u `platform/windows.py`
  (`NotSupported`) ostaju bosanske — nisu korisnički tekst, ali su vidljive u
  rijetkim putanjama; README to izričito kaze.
  USPUT POPRAVLJEN BUG: MCP pokrenut po putanji nije mogao `import mujofix`
  (novi i18n import u `validate_plan`) — `mujofix_mcp.py` sada dodaje korijen
  repoa na `sys.path` (isti obrazac kao ostali moduli). 243 testa.
- I18N-NALAZI 2026-10-22 (ZAVRSENO, 9/9): `ScanContext.lang` + `Scanner.t()`
  (jezik na instanci, postavlja ga `scan()`, pa ga vidi i `unavailable_reason`).
  Migrirani: disk, startup, services, config, drivers, duplicates, network,
  permissions, suspicious + base "skipped"/greska stringovi. `scan --lang bs|en`
  i lokalizovan `summarize`. 116 `sc_*` kljuceva (bs+en). Cuvar
  `tests/test_scanner_i18n.py`: (a) ratchet — title/why/impact/risk MORAJU kroz
  `self.t(...)`, `unavailable_reason` isto (dijakritike nisu dovoljan signal:
  mnogo bosanskog teksta je ASCII); (b) svaki scanner u "en" bez bosanskih
  znakova; (c) na Linuxu svi "skipped" razlozi na engleskom; (d) deterministicki
  disk test (lazni disk_usage) na oba jezika. Dokaz izvrsenjem:
  `scan --lang en --summary` -> "Your computer has 4 problems.";
  `NetworkScanner` -> "A proxy is enabled for internet traffic";
  `SuspiciousScanner` skipped -> "process list and signatures are read only on
  Windows". 237 testova.
- I18N-NALAZI 2026-10-22 (pocelo, 1/9): engleski UI je prikazivao bosanski
  tekst nalaza. Uveden `ScanContext.lang` + `t(ctx, key)` u scannerima;
  `disk` scanner migriran (22 kljuca), `scan --lang bs|en` i lokalizovan
  `summarize`. Cuvar `tests/test_scanner_i18n.py` sa ratchet listom
  (`MIGRATED = {"disk"}`). Ostali scanneri: 8/9 preostalo.
  USPUT NADJEN I POPRAVLJEN PRAVI DEFEKT: `MujoFixCLI.exe` je na Windowsu PAO
  (`UnicodeEncodeError`) na dijakriticima koje sam uveo — legacy code page.
  Dokaz: CI `installer-windows` failure ("frozen scan exit 1 :: Traceback ..."),
  lokalna reprodukcija sa `PYTHONIOENCODING=ascii`. Sada `force_utf8_console()`
  prebacuje stdout/stderr na UTF-8 (`errors="replace"`).
- OFFLINE 2026-10-22: offline objašnjenje (koje većina korisnika vidi, jer
  besplatni Zen tier odbija poziv iz naseg CLI-a) bilo je jedan red sablona.
  Sada `offline_explain(finding, lang)` gradi iz PODATAKA nalaza: why/impact/
  risk (+reverzibilno)/dokaz (dict -> `k=v`)/tehnicki detalji + koja akcija
  postoji u katalogu (ili izricito da nema). Polja koje nalaz nema se
  IZOSTAVLJAJU — nikad se ne popunjava pretpostavkom; test
  `test_offline_never_invents_missing_fields`. Dvojezicno (bs/en) preko i18n,
  ukljucujuci note linije (`ai_note_*`) i `ai_none`. 6 novih testova.
  ZAVRSENO 2026-10-22 (isti dan): svi skeneri (9/9) + base "skipped" stringovi
  su migrirani — nalazi, offline objasnjenja i CLI izlaz su dvojezicni.
- KARANTIN-PREGLED 2026-10-22: fajlovi iz RANIJIH sesija bili su nedostupni —
  "Poništi sve" (`self._undone`) zna samo za tekuću sesiju, pa je poslije
  restarta preostajalo samo trajno brisanje. Sada `list_quarantine` /
  `load_quarantine_index` / `restore_quarantine_file` (originalna putanja iz
  manifesta; odbija pregaziti postojeci fajl; bez manifesta dize razlog) i
  `ui/quarantine.py` dijalog (lista + "Vrati odabrano"/"Obriši odabrano").
  Testovi: 3 unit (`tests/test_quarantine.py`) + 2 GUI (`test_faza4b`).
- KARANTIN 2026-10-22 (nadjen stvarni defekt, ne samo dokumentacija): karantin
  se NIKAD nije cistio — `%LOCALAPPDATA%\MujoFix\quarantine` je rastao
  zauvek, a izvjestaj je mogao tvrditi "oslobodjeno" za fajlove koji su samo
  premjesteni (isti disk). Sada: `quarantine_file` pamti `size` prije
  premjestanja; `quarantine_usage()`/`purge_quarantine()` u `actions/base.py`;
  GUI dugme "Očisti karantin" (broj fajlova + GB, potvrda, upis "Oslobođeno: X"
  u izvjestaj; otkazivanje ne brise nista). Testovi: `tests/test_quarantine.py`
  (4) + 3 GUI. CHANGELOG otvoren kao 0.4.0 (u razvoju) da dev build ne tvrdi
  0.3.0.
- OBJAVLJENO 2026-10-22: **v0.3.0** (tag + GitHub Release). CI `build` job
  zelen: pin provjera, OpenCode download + SHA-256, PyInstaller, smoke
  zapakovanog CLI-ja, Inno installer, SHA256SUMS, Release. Asseti:
  `MujoFix-Setup-0.3.0.exe` (76 MB, sha256
  e0eb1002505779e897868f94d687b6c7c8108138f634a4480be8ec6a51494bf2),
  `MujoFix-v0.3.0.zip` (115 MB), `SHA256SUMS.txt`.
  Ziv update put provjeren protiv stvarnog release-a: korisnik na 0.2.0 ->
  available=True, latest 0.3.0, izabran `MujoFix-Setup-0.3.0.exe`; korisnik na
  0.3.0 -> available=False. README (bs+en) i badge podignuti na 0.3.0.
- VERZIJA 2026-10-21: `[Unreleased]` u CHANGELOG-u je zatvoren kao **0.3.0**
  (build iz main-a je prije prijavljivao 0.2.0 — isto kao izdata verzija, pa bi
  `update` i ime instalera bili pogresni). `mujofix/version.py` fallback
  podignut na 0.3.0. **NIJE tagovano ni objavljeno** — README i badge i dalje
  pokazuju izdatu 0.2.0 (njeni asseti postoje); release 0.3.0 ceka odluku.
- PAKOVANJE 2026-10-21 (dokaz na hostu, ne samo kompajliranje): PyInstaller
  build po `mujofix.spec` prolazi (Linux ignorise `.ico` uz upozorenje), a
  ZAMRZNUTI exe stvarno radi: `dist/MujoFix/MujoFixCLI scan --summary` -> "4
  problema", `update` -> "Verzija 0.2.0 je najnovija", GUI (`MujoFix`)
  se pokrene (offscreen smoke). U bundleu su `_internal/assets/mujofix.ico`
  (za ikonu prozora) i `CHANGELOG.md` (version.py ga cita u runtime-u).
  Uklonjen suvisan `mujofix/i18n` datas unos (modul ide u PYZ; kopija je
  nosila i `__pycache__`). CI: novi smoke korak u `installer-windows` na svakom
  push-u (prije je dist samo kompajliran; `build` job je imao smoke ali je
  tag-only). Uz to `tests/test_workflows.py` hvata YAML trap (ne-citiran
  `name:` sa ": ") koji tiho ugasi CI — bez PyYAML zavisnosti.
- DNEVNIK 2026-10-21 (dokumentovana praznina zatvorena): README je za
  "audit log (JSON)" písao da nije implementiran. Sada novi `mujofix/audit.py`
  (cist modul) + GUI: poslije svake popravke (i u dry-run) upisuje se
  `audit-<vrijeme>.json` u `%LOCALAPPDATA%\MujoFix\audit` sa svim fazama
  koraka (`Runner.audit`) i sazetkom; putanja ide u log, a kvar dnevnika ne
  rusi app. Testovi: `tests/test_audit.py` (3) + GUI testovi da se fajl upise
  (apply i dry-run). 206 OK.
- UX 2026-10-21 (nedovrseno -> dovrseno): (1) ikona — `mujofix.spec` je imao
  `icon="NONE"` i installer `SetupIconFile` nije imao, pa je instaliran app nosio
  genericku Python/Qt ikonu; sada `assets/mujofix.ico` (multi-size, PNG payload,
  `scripts/make_icon.py`, bez novih zavisnosti) + spec/iss/theme/testovi.
  (2) izbor jezika — `lang` je bio provucen svuda ali se NIJE mogao izabrati;
  sada combo (bs/en) u UI-ju, pamti se u QSettings i primjenjuje pri sljedecem
  pokretanju. (3) prozor pamti velicinu/poziciju (`saveGeometry/restoreGeometry`).
  Testovi: `test_language_choice_is_saved_and_needs_restart`,
  `test_window_geometry_is_restored`, `tests/test_icon.py` (6). 201 OK.
- DIZAJN 2026-10-21 (Fluent 2 / Windows 11): novi `mujofix/ui/theme.py` —
  QSS tokeni (Fluent 2 boje, radius 4/8, akcent iz Windows DWM AccentColor,
  fallback brand plava), font stack Segoe UI Variable/Segoe UI, automatska
  svijetla/tamna tema (`AppsUseLightTheme` iz registryja; `MUJOFIX_THEME`
  override), Mica preko `DwmSetWindowAttribute` (backdrop 2 + round corners +
  extend frame). `theme.setup(app, window)` prvo postavi solidnu temu, pa
  Mica SAMO ako DWM poziv vrati 0 — ako padne, translucent se ponistava, pa
  prozor nikad ne ostane providan. Van Windowsa sve graceful (Mica False).
  Widgeti dobili objectName (root/subtitle/h1/report/log/findings/primary).
  Testovi: `tests/test_theme.py` (9). NEPROVJERENO (VM): izgled Mica na
  pravom Win11 (DWM) — na hostu (Linux) Mica je uvijek False.
- ISPRAVLJENO 2026-10-18 (engleski UI je curio bosanski): hardkodovan tekst
  van `tr()` — naslovi i dugmad ekrana pristanka ("Prihvatam AI"/"Ostajem
  offline"), naslov pregleda poslanog, i log poruke u main_window. Sada svi
  idu kroz `tr()` (consent/sent-log dobili parametar `lang`), dodat
  `CATEGORIES_EN`. Cuvar `test_no_hardcoded_bosnian_text_in_ui` pada ako se
  vrati hardkodovan tekst; `test_english_consent_dialog_is_translated`
  provjerava stvarni tekst dialoga na engleskom.
- DODANO 2026-10-18: `tests/test_i18n.py` — cuvar da bs/en imaju iste kljuceve,
  da nema praznih prijevoda i da svaki `tr()`/`_t()` kljuc iz koda postoji
  (nepostojeci kljuc se u UI prikazivao kao sirovo ime kljuca).
- ISPRAVLJENO 2026-10-18 (obećanje bez prekidaca): ekran pristanka kaze "AI
  se može isključiti bilo kad", a `ConsentDialog` se prikazivao SAMO kad
  izbora nema — ko jednom pristane, nije mogao vratiti offline (niti ponovo
  ukljuciti). Sada postoji dugme "AI: uključi/isključi"
  (`MainWindow.open_consent_settings`) koje uvijek otvara isti izbor, prikazuje
  trenutno stanje, i loguje stvarno stanje poslije izbora. Testovi:
  `test_ai_can_be_turned_off_after_consent` (izbor off -> log + sljedece
  objasnjenje ide offline lancem), `test_settings_button_exists_after_consent`.
  Ukupno 174, OK.
- ISPRAVLJENO 2026-10-18 (izolacija je bila laz): config se MERGE-ovao sa
  korisnickim globalnim `~/.config/opencode`, pa je nas agent naslijedio
  globalne MCP servere i pluginove. Dokazano protiv pinovanog binarnog
  (`GET /config` sa i bez `XDG_CONFIG_HOME`): bez izolacije MCP =
  [context7, gitnexus, mujofix, playwright] i 8 pluginova; sa izolacijom MCP =
  [mujofix], 0 pluginova. Uz `mcp_*: true` to je znacilo da nas agent ima
  playwright (browser) i pluginove koji izvrsavaju tudji kod — suprotno tvrdnji
  "izolirani opencode.json". Sada `build_chain` dize server sa
  `XDG_CONFIG_HOME=<workdir>/config-home` (`agent_config.config_home`).
  Kredencijali (auth.json) su u DATA diru, ne u config diru, pa zivi model
  ostaje prijavljen — dokazano: `opencode auth list` sa izolovanim
  XDG_CONFIG_HOME cita isti `~/.local/share/opencode/auth.json`. Testovi: `TestIsolatedConfigHome` (2). Ukupno 172, OK.
  NEPROVJERENO (VM): da li pinovani binarni na Windowsu postuje
  XDG_CONFIG_HOME (na Linuxu dokazano) — ako ne, izolacija ne radi na Win.
  NEPROVJERENO (VM): da li pinovani binarni na Windowsu postuje
  XDG_CONFIG_HOME.
  NEPROVJERENO (nema Zen auth na dev masini): uspjesan poziv besplatnog
  `opencode/*` modela. Na ovoj masini je jedini kredencijal OpenRouter, pa
  `run --model opencode/beam-free` vrati prazan odgovor -> provider baci
  ProviderError -> lanac iskreno padne na offline (bez lazne tvrdnje).
- ISPRAVLJENO 2026-10-18 (AI plan je bio mrtav kod): `_on_explained` je
  ignorisao `resp.plan` — plan se validirao i onda bacao, pa je README
  obećavao plan koji korisnik nikad ne vidi. Sada se plan prikaže u logu kao
  citljiva lista (`plan_lines`, labele za akcije iz kataloga). Primjena ostaje
  deterministicka: akcije iz ODABRANIH nalaza, sa snapshot/rollback-om i
  verifikacijom. Direktna primjena AI koraka (meta iz plana) ostaje za VM
  provjeru — model predlaze `target`, pa bi se morao dokazati protiv
  evidencije scannera prije izvrsenja. Testovi: `TestPlanLines` (3) +
  `test_ai_plan_is_shown_not_silently_dropped`. Ukupno 170, OK.
- ISPRAVLJENO 2026-10-18 (zivi put, halucinacija + kontradikcija):
  sistem-prompt je tvrdio "You receive PC findings ONLY as tool data from the
  mujofix MCP server", a u zivom putu `get_findings` vraca prazno (snimak se
  ucitava samo preko `--findings`) — nalazi su u poruci. Agent bi zakljucio da
  nema nalaza. Jos gore: `get_system_info` je bez snimka vracao LAZNI fixture
  ("spike" podaci) modelu koji ne smije izmisljati brojeve. Sada: prompt kaze
  da nalazi dolaze kao podaci u poruci, MCP sluzi katalogu + validaciji plana,
  a prazan snimak daje postenu `note` (bez laznih vrijednosti); `get_evidence`
  vise ne vraca "spike-fixture" string. Testovi: `test_empty_store_returns_
  honest_note_not_fake_data`, `test_loaded_snapshot_is_served_verbatim`,
  `test_prompt_matches_real_data_path`. Ukupno 166, OK.
- ISPRAVLJENO 2026-10-18 (pristanak): ekran je prikazivao scan payload
  (`{"findings": ...}`) pod natpisom "stvarni payload", a modelu ide prompt
  tekst. Sada i ekran i provider koriste istu funkciju (`build_prompt`) nad
  istim anonimiziranim nalazima — prikaz ne moze odlutati od zahtjeva.
  Test: `test_consent_example_is_exactly_the_sent_prompt`. Ukupno 163, OK.
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
- `mujofix/ai/opencode_runtime.py` — (2026-10-21: bez servera) `bundled_binary`/`FORBIDDEN_FLAGS`; ranije `opencode serve`: 127.0.0.1,
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
- 8 akcija: disable_startup_item (HKCU/HKLM, UAC samo za HKLM),
  clean_temp (starije od 7 dana u karantin, manifest), restart_service (`sc`,
  UAC), remove_hosts_entry (hosts zapis, UAC; snapshot cuva cijeli fajl),
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
