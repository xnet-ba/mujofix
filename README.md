<div align="center">

# 🛠️ MujoFix

### AI mehaničar za Windows računar

**Klikneš SCAN — aplikacija nađe probleme, prevede ih u običan jezik, predloži plan popravki, ti odobriš, ona popravi, provjeri i vrati nazad ako nešto pođe po zlu.**

[![Status](https://img.shields.io/badge/status-v0.4.0-blue)](docs/STATUS.md)
[![Licenca](https://img.shields.io/badge/licenca-MIT-green)](LICENSE)
[![Platforma](https://img.shields.io/badge/Windows-10%20%7C%2011-blue)](docs/STATUS.md)
[![Python](https://img.shields.io/badge/Python-3.11%2B-yellow)](AGENTS.md)

[Šta je MujoFix](#-šta-je-mujofix) •
[Kako radi](#-kako-radi) •
[Moduli](#-moduli-skeniranja) •
[AI sloj](#-ai-sloj) •
[Sigurnost](#-sigurnost-i-povratak-stanja) •
[Status](#-status-projekta)

</div>

---

## <h2>❓ Šta je MujoFix</h2>

<p>MujoFix je <b>open-source desktop aplikacija</b> koja običnom korisniku — bez ikakvog admin znanja — pomaže da održava Windows računar zdravim. Umjesto tehničkih poruka o greškama, korisnik dobija rečenice poput:</p>

> <p><b>"Tvoj računar ima 7 problema.<br>🔴 2 ozbiljna &nbsp; 🟠 3 srednja &nbsp; 🟢 2 mala<br>Automatski se može popraviti: 4."</b></p>

<p>…i jedno dugme <b>[ POPRAVI SVE ]</b>. Ispod se nalazi proširiva lista s detaljima (<i>"Prikaži tehničke detalje"</i>) za naprednije korisnike.</p>

<table>
  <tr>
    <th>Podržano</th>
    <th>Detalj</th>
  </tr>
  <tr>
    <td>🖥️ Sistem</td>
    <td>Windows 10 (22H2) i Windows 11 (23H2+), x64</td>
  </tr>
  <tr>
    <td>👤 Korisnik</td>
    <td>Bez admin znanja; radi i <b>bez admin prava</b> (čitanje + popravke u korisničkom profilu)</td>
  </tr>
  <tr>
    <td>🔐 UAC</td>
    <td>Elevacija se traži <b>samo kad je potrebno</b>, uz objašnjenje zašto — prije nego iskoči Windows prozor</td>
  </tr>
  <tr>
    <td>🌐 Jezik</td>
    <td>Bosanski/hrvatski/srpski (default), i18n struktura za engleski</td>
  </tr>
  <tr>
    <td>📶 Offline</td>
    <td>Aplikacija ostaje <b>potpuno upotrebljiva bez interneta i bez AI-ja</b> (offline mod)</td>
  </tr>
</table>

---

## <h2>🔄 Kako radi</h2>

<ol>
  <li><b>SCAN</b> — moduli skeniranja (izvršavaju se redom) uz progres bar i mogućnost otkazivanja. Greška modula ne ruši aplikaciju — postaje <i>skipped</i> u izvještaju.</li>
  <li><b>ANALIZA</b> — svaki nalaz ima ozbiljnost (<code>CRITICAL / MEDIUM / LOW</code>), procjenu uticaja, rizik popravke i oznaku da li je popravka reverzibilna.</li>
  <li><b>PRIKAZ</b> — jednostavan sažetak običnim jezikom + proširiva lista detalja. Izgled: <b>Fluent 2 / Windows 11</b> (Segoe UI, zaobljene kontrole, automatska svijetla/tamna tema) i <b>Mica</b> pozadina kad je DWM pruža (Win11; u suprotnom solidna boja). Izbor jezika (<b>Bosanski / English</b>, primjenjuje se pri sljedećem pokretanju) i zapamćena veličina/pozicija prozora. <b>Dvojezično je sve što korisnik vidi:</b> interfejs, nalazi skenera (naslov, zašto, uticaj, rizik), poruke akcija (precondition/apply/verify/rollback), nazivi i rizik akcija u katalogu, razlozi validacije AI plana, offline objašnjenja, izvještaj i CLI izlaz. (Tehničke poruke izuzetaka u platformskom sloju ostaju na bosanskom.)</li>
  <li><b>PLAN</b> — AI predloži plan popravki (koraci + redoslijed), koji se prikaže uz objašnjenje; svaki predlog prolazi katalog akcija i validator prije nego se uopšte prikaže. Primjenjuju se akcije <b>odabranih nalaza</b> (deterministički, sa snapshot/rollback tačkom i verifikacijom) — korisnik odobrava: <b>sve, pojedinačno ili ništa. Bez odobrenja se NIŠTA ne mijenja.</b></li>
  <li><b>IZVRŠENJE</b> — prije svakog koraka snapshot/rollback tačka, pa izvršenje.</li>
  <li><b>VERIFIKACIJA</b> — nakon svakog koraka ponovo se izmjeri isto što je nalaz detektovao i potvrdi da je problem stvarno riješen.</li>
  <li><b>ROLLBACK</b> — ako verifikacija padne ili se stanje pogorša, korak se <b>automatski vraća</b> i korisnik se izvijesti.</li>
  <li><b>SAŽETAK</b> — koliko je problema, po ozbiljnosti, i <b>koliko ih se može automatski popraviti</b> (nalazi bez akcije su preporuke).</li>
  <li><b>IZVJEŠTAJ</b> — broj popravljenih / preskočenih / neuspjelih koraka, <b>koliko je u karantinu</b> i, poslije čišćenja, <b>oslobođeni GB</b> + opcija <b>"Poništi sve"</b> preko rollback tačaka. (Vrijeme boot-a se ne mjeri nigdje u kodu — vidi <code>scanners/startup.py</code>.)</li>
</ol>

<details>
<summary><b>Zašto svaki nalaz mora imati dokaz?</b></summary>
<p>AI smije govoriti <b>samo o podacima koje je scanner stvarno prikupio</b> (sirova mjerenja, ključevi registra, event ID-jevi, putanje). Bez dokaza nalaz se ne prikazuje. Kad je AI nesiguran, mora to izričito reći. Zabranjeno: izmišljeni procenti, brojke i tvrdnje o uzroku bez dokaza.</p>
</details>

---

## <h2>🖼️ Izgled</h2>

<p>Fluent 2 / Windows 11: Segoe UI, zaobljene kontrole, automatska svijetla/tamna
tema i Mica pozadina na Win11. Snimke su sa stvarne aplikacije (offscreen
render na pravom Windows 11, bs jezik):</p>

<p align="center">
  <img src="docs/screenshots/mujofix-light.png" alt="MujoFix — svijetla tema" width="520">
  <img src="docs/screenshots/mujofix-dark.png" alt="MujoFix — tamna tema" width="520">
</p>

---

## <h2>🧩 Moduli skeniranja</h2>

<p>Svi moduli su pluginovi s istim interfejsom (<code>scan()</code> nikad ne ruši aplikaciju — greška postaje <i>skipped</i> izvještaj). Svaki modul provjerava verziju Windowsa i graceful se isključuje gdje nije podržan.</p>

<table>
  <tr><th>Modul</th><th>Šta gleda</th><th>Faza</th></tr>
  <tr><td>🚀 Startup</td><td>Run/RunOnce ključevi, Startup folder, Taskovi, auto-servisi</td><td>1 ✅</td></tr>
  <tr><td>🔁 Servisi</td><td>Servisi koji se ruše (Event ID 7031/7034), neočekivana stanja</td><td>1 ✅</td></tr>
  <tr><td>💾 Disk</td><td>Slobodan prostor, temp, WU keš, recycle bin, Windows.old, SMART</td><td>1 ✅</td></tr>
  <tr><td>📁 Veliki fajlovi i duplikati</td><td>Veličina → djelimični hash → puni hash; duplikati se <b>nikad ne brišu automatski</b></td><td>5</td></tr>
  <tr><td>🔧 Drajveri i paketi</td><td>Stari drajveri (pnputil), zaostali instaleri, nekorišteni programi</td><td>5</td></tr>
  <tr><td>⚙️ Konfiguracija</td><td>PATH, env varijable, hosts, power plan, SFC/DISM indikatori</td><td>5</td></tr>
  <tr><td>🌐 Mreža</td><td>DNS, proxy, adapteri, latencija, hosts hijack, Winsock</td><td>5</td></tr>
  <tr><td>🕵️ Sumnjivi procesi</td><td>Nepotpisani procesi na čudnim lokacijama, autostart iz Temp-a, <b>Defender izuzeci</b> (i isključena real-time zaštita). <b>Ne tvrdi "virus"</b> — kaže "sumnjivo, razlozi: …"; izuzeci su <b>samo čitanje</b></td><td>5</td></tr>
  <tr><td>⏰ Zakazani zadaci</td><td>Zadaci koji se pokreću pri prijavi/boot-u, a program im je izvan sistemskih foldera (Task Scheduler)</td><td>5</td></tr>
  <tr><td>🛡️ Sigurnosna postavka (samo čitanje)</td><td>BitLocker na sistemskom disku, Secure Boot, TPM, Windows Update servis — <b>samo prijavljuje, ništa ne mijenja</b></td><td>5</td></tr>
  <tr><td>🔒 Permisije</td><td>Preširoke ACL dozvole, svijet-zapisivi folderi u PATH-u, UAC, share-ovi</td><td>5</td></tr>
</table>

---

<!-- coverage:start -->
<p>Od <b>32</b> nalaza, <b>12</b> ima automatsku popravku (akcija iz kataloga, sa snapshot/verify/rollback); ostali su <b>namjerno samo preporuke</b> — sa razlogom:</p>

| Nalaz | Popravka | Napomena |
|---|---|---|
| `config-path-writable` | ❌ | samo POSIX (na Windowsu ACL nije mode); skidanje prava pisanja je rizično |
| `config-path-missing` | ✅ remove_path_entry | |
| `config-temp-var` | ✅ fix_temp_var | |
| `config-power-saver` | ✅ disable_power_saver | |
| `config-sfc` | ❌ | traži `sfc /scannow` (duga popravka sistema, van kataloga) |
| `disk-almost-full` | ❌ | uzrok je širok — temp i WU keš imaju svoje nalaze |
| `disk-low` | ❌ | uzrok je širok — temp i WU keš imaju svoje nalaze |
| `disk-temp` | ✅ clean_temp | |
| `disk-wu-cache` | ✅ clean_temp | |
| `disk-windows-old` | ❌ | brisanje je NEPOVRATNO (nema povratka na staru verziju) |
| `drivers-old` | ❌ | update drajvera traži proizvođački alat i restart (rizik plavog ekrana) |
| `duplicates-found` | ✅ quarantine_duplicates | |
| `network-dns` | ❌ | dijagnostika — uzrok je ruter/provajder, ne računar |
| `network-unreachable` | ❌ | dijagnostika — uzrok je firewall/provajder |
| `network-slow` | ❌ | dijagnostika — uzrok je mreža/provajder |
| `network-hosts` | ✅ remove_hosts_entry | |
| `network-proxy` | ✅ disable_proxy | |
| `network-winsock` | ❌ | `netsh winsock reset` traži restart i mijenja mrežni stek |
| `permissions-uac-off` | ❌ | uključivanje UAC-a traži restart (može zaključati zavisne programe) |
| `permissions-acl` | ❌ | zatezanje ACL-a može slomiti pristup — rizično bez pregleda |
| `permissions-shares` | ✅ remove_share | |
| `permissions-path-writable` | ❌ | samo POSIX fallback; isto kao config-path-writable |
| `bitlocker-off` | ❌ | mijenjanje zaštitnih politika je IZVAN politike app-a — samo prijavljujemo |
| `secureboot-off` | ❌ | isto — boot politika se ne dira iz aplikacije |
| `tpm-absent` | ❌ | hardverski nedostatak — nema šta da se popravi softverski |
| `wuauserv-disabled` | ❌ | politika ažuriranja je izvan politike app-a — samo prijavljujemo |
| `services-auto-stopped` | ✅ restart_service | |
| `startup-count` | ✅ disable_startup_item | |
| `suspicious-process` | ❌ | namjerno report-only — app ne gasi procese i ne tvrdi da je virus |
| `suspicious-defender-off` | ❌ | app nikad ne dira antivirus/zaštitu (politika) |
| `defender-exclusions` | ❌ | mijenjanje zaštitnih politika je IZVAN politike app-a — samo prijavljujemo |
| `tasks-autostart-untrusted` | ✅ disable_task | |
<!-- coverage:end -->

## <h2>🚫 Šta aplikacija NE radi (iskreno)</h2>

<ul>
  <li><b>Ne mjeri vrijeme boot-a.</b> Startup nalaz broji stavke i to izričito kaže; stvarno vrijeme podizanja se ne mjeri nigdje u kodu.</li>
  <li><b>Ne pravi System Restore Point.</b> Sigurnosna mreža je snapshot po akciji + rollback + karantin (traži admin/Checkpoint-Computer).</li>
  <li><b>Ne instalira drajvere ni Windows zakrpe.</b> Zastarjeli drajveri i isključen Windows Update se <i>prijavljuju</i>, ne popravljaju.</li>
  <li><b>Ne mijenja zaštitne politike:</b> Defender (izuzeci, real-time), UAC, BitLocker, Secure Boot, deljeni folderi, firewall — sve je <b>samo čitanje + preporuka</b>.</li>
  <li><b>Ne gasi procese</b> i nikad ne tvrdi „virus" — sumnjivi nalazi kažu „sumnjivo, razlozi: …".</li>
  <li><b>Ne briše trajno bez tvoje potvrde.</b> Fajlovi idu u karantin; trajno briše samo dugme „Očisti karantin" (uz potvrdu) i to se upiše u dnevnik.</li>
  <li><b>Karantin nema automatski rok.</b> Ništa se ne briše samo — dok ti ne očistiš, fajlovi stoje u <code>%LOCALAPPDATA%\MujoFix\quarantine</code>.</li>
  <li><b>Nema telemetrije.</b> Mreža se koristi samo za: provjeru ažuriranja (GitHub), AI objašnjenje (uz pristanak, anonimizirano) i mrežnu dijagnostiku (DNS/TCP probe ka javnom DNS-u).</li>
  <li><b>AI ništa ne izvršava.</b> Model objašnjava i predlaže; izvršava samo deterministički katalog akcija, uz tvoje odobrenje. Ako besplatni model nije dostupan, lanac iskreno pada na offline.</li>
  <li><b>Radi samo na Windowsu</b> (10 22H2+ / 11). Na drugim sistemima se scanneri iskreno preskaču (CLI se pokreće, ali nema šta da skenira).</li>
  <li><b>Build nije potpisan</b> — SmartScreen upozorenje je očekivano, ne bug.</li>
  <li><b>Puna VM matrica (čist Win10/Win11) je otvorena.</b> Sve što nije izvršeno na pravom Windowsu stoji označeno kao <i>netestirano</i> (<a href="docs/TESTING.md">docs/TESTING.md</a>).</li>
</ul>

---

## <h2>🤖 AI sloj</h2>

<p>MujoFix koristi <b>OpenCode</b> (pinovana, testirana verzija, MIT licenca) kao AI motor — instalira se zajedno s aplikacijom, korisnik ne instalira ništa ručno (ni Node ni npm).</p>

<pre>
MujoFix UI → MujoFix Core (scanneri, katalog, executor, rollback)
                    │
                    └── OpenCode child proces (opencode run, bez servera/porta)
                              │
                              └── MujoFix MCP server (samo 5 alata, svi read-only + validator)
</pre>

<ul>
  <li><b>Izvršenje je ISKLJUČIVO u Coreu.</b> OpenCode objašnjava i predlaže, validator provjerava (JSON schema + allowlista), korisnik odobrava, deterministički executor izvršava. OpenCode nikad ne izvršava komande.</li>
  <li>Agent <code>mujofix</code>: <b>svi ugrađeni alati zabranjeni</b> (bash, edit, write, web…), dozvoljeni samo MujoFix MCP alati, deny po defaultu.</li>
  <li><b>Fallback lanac:</b> model A → B → C → <b>OFFLINE mod</b>. Offline objašnjenje je dvojezično i gradi se <b>isključivo iz podataka koje je scanner prikupio</b> (zašto, uticaj, rizik, dokaz, tehnički detalji + koja akcija postoji) — bez ijedne pretpostavke i bez AI-ja.</li>
  <li><b>Živi model:</b> uz pristanak MujoFix pokrene <code>opencode run</code> kao <b>child proces</b> i koristi <b>besplatan Zen model</b> (npr. <code>opencode/beam-free</code>). <b>Nema lokalnog backend-a</b>: ne diže se <code>opencode serve</code>, nema porta ni lozinke, ništa se ne izlaže na mrežu — MujoFix je isključivo instalabilna Windows aplikacija. Ako binary ili besplatni model nisu dostupni — tiho nazad na <b>offline</b>, uz iskrenu poruku o razlogu (bez lažne tvrdnje da je AI radio). <i>netestirano</i>: živi put još nije pokrenut na Windows VM-u (<a href="https://github.com/xnet-ba/mujofix/issues/1">Issue #1</a>).</li>
  <li><b>Privatnost:</b> prije prvog korištenja AI-ja — ekran pristanka (koji podaci idu, kome, primjer payload-a). Anonimizacija prije slanja; default je offline dok korisnik ne pristane. <b>Besplatni Zen modeli nisu privatni</b> (potvrđeno iz <a href="https://opencode.ai/legal/terms-of-service">ToS</a> i <a href="https://opencode.ai/v2/docs/console/models/">Zen docs</a>, 2026-10-18): provajderi su uglavnom zero-retention, ali za neplaćene račune sadržaj se smije koristiti za unapređenje usluge, pojedini besplatni modeli tokom promo perioda mogu koristiti poslane podatke za poboljšanje modela, dio zahtjeva (OpenAI/Anthropic) čuva se 30 dana.</li>
</ul>

---

## <h2>🛡️ Sigurnost i povratak stanja</h2>

<ul>
  <li><b>Zaštićene zone</b> (hard-coded crna lista u validatoru AI plana): System32, WinSxS, Program Files, korisnički Dokumenti/Slike/Desktop/Download, boot konfiguracija (BCD), BitLocker, Defender. Namjerno NIJE na listi cijeli <code>C:\Windows</code> — <code>Windows\Temp</code> i WU cache su legitimni ciljevi. Izvršni sloj ipak vrti samo akcije iz kataloga nad nalazima koje je korisnik odabrao.</li>
  <li><b>Prije popravke:</b> <b>vlastiti manifest po akciji</b> — snapshot vraća tačno stanje koje akcija mijenja (npr. prijašnja vrijednost registry unosa ili stanje servisa/taska) + <b>karantin fajlova</b> (ne trajno brisanje: u karantin idu fajlovi stariji od 30 dana). Dugme <b>„Karantin"</b> prikazuje šta je unutra i vraća pojedinačne fajlove (i one iz ranijih sesija — originalna putanja se čita iz manifesta; fajl bez manifesta se može samo obrisati). Dugme <b>„Očisti karantin"</b> jedino trajno briše — prikaže koliko fajlova i koliko GB, traži potvrdu i u izvještaj upiše <b>oslobođeno</b>. <b>System Restore Point nije implementiran</b> (traži admin/Checkpoint-Computer; vidi <code>docs/STATUS.md</code>) — sigurnosna mreža je snapshot + rollback po akciji.</li>
  <li><b>Svaka akcija:</b> precondition → snapshot → apply → verify → rollback ako zatreba. Akcija bez <code>rollback()</code> ne smije biti auto-fix.</li>
  <li><b>Probni (dry-run) mod</b> (checkbox u GUI-ju: ništa se ne mijenja) i <b>čítljiv dnevnik</b> svakog koraka u prozoru (precondition / snapshot / apply / verify / dry-run). Poslije svake popravke upisuje se i <b>JSON dnevnik izvršavanja</b> u <code>%LOCALAPPDATA%\MujoFix\audit\audit-&lt;vrijeme&gt;.json</code> (sve faze koraka + sažetak; putanja se ispiše u dnevniku).</li>
  <li><b>Nikad:</b> gašenje antivirusa/firewalla/Windows Update-a, mijenjanje zaštitnih politika.</li>
</ul>

---

## <h2>🚦 Status projekta</h2>

<table>
  <tr><th>Faza</th><th>Sadržaj</th><th>Stanje</th></tr>
  <tr><td><b>0 — SPIKE</b></td><td>Bundlovani OpenCode kao child, besplatni modeli, MCP alat, zabrana shell-a, offline</td><td>🟢 kod + dokaz na hostu (1–2); 3–5 čekaju živi model</td></tr>
  <tr><td><b>1</b></td><td>Skeleton + CLI scanner (startup, disk, servisi) + model nalaza</td><td>🟢 gotovo (Linux + host dokazi)</td></tr>
  <tr><td><b>2</b></td><td>Action katalog + runner (snapshot/verify/rollback)</td><td>🟢 gotovo (katalog 10 akcija; 3 potvrđene host dokazom, ostale testovi — vidi <a href="docs/TESTING.md">TESTING</a>)</td></tr>
  <tr><td><b>3</b></td><td>GUI (sažetak, plan, odobravanje, progres, izvještaj)</td><td>🟢 gotovo (GUI smoke na hostu)</td></tr>
  <tr><td><b>4</b></td><td>Puni AI sloj (MCP, validator, fallback, pristanak, offline)</td><td>🟢 kod gotov (offline default; Zen ToS neprovjeren)</td></tr>
  <tr><td><b>5</b></td><td>Preostali moduli (mreža, drajveri, duplikati, procesi, permisije…)</td><td>🟢 gotovo (10 scannera; 9 potvrđeno host dokazom 2026-10-14, `tasks` dodat 2026-10-22)</td></tr>
  <tr><td><b>6</b></td><td>Installer, potpisivanje, auto-update, javni release</td><td>🟡 kod gotov; build/release odluka otvorena (nepotpisan)</td></tr>
</table>

<p><b>Validacija na pravom Windows 11 (2026-10-23, laptop, Enterprise N sa WDAC enforced):</b> scan 11/11 scannera bez skipova, <b>host_proof 12/12 PASS</b> (apply → verify → rollback, uključujući nove akcije hosts/share/power), pinovani opencode prihvata naš config (agent `mujofix`, svih 11 alata `deny`), CLI bs/en + JSON nalaza + živa provjera update-a — dokazi u <a href="lab/results-win11-laptop/">lab/results-win11-laptop/</a>. Ranije: <i>host-direct</i> na drugom Win11 računaru (scan 9/9 u tom runu, 3 akcije uz identičan rollback, GUI smoke, spike 1–2). Puna VM matrica (Win10 + Win11, čist sistem) ostaje kao opciona, produžena validacija — vidi <a href="docs/TESTING.md">docs/TESTING.md</a>.</p>

<p>Detalji po sesiji: <a href="docs/STATUS.md">docs/STATUS.md</a> • Pravila za kodere: <a href="AGENTS.md">AGENTS.md</a></p>

## <h2>⬇️ Instalacija (Windows, EXE)</h2>

<p>Preuzmi sa <a href="https://github.com/xnet-ba/mujofix/releases">Releases</a> stranice:</p>

<ol>
  <li><b><code>MujoFix-Setup-&lt;verzija&gt;.exe</code></b> — preporučeno (instalater), ili
      <b><code>MujoFix-v&lt;verzija&gt;.zip</code></b> — portabilna verzija (raspakuj i pokreni <code>MujoFix.exe</code>).</li>
  <li><b>Provjeri hash</b> (opciono, ali preporučeno) — uz release ide <code>SHA256SUMS.txt</code>:
<pre># PowerShell, u folderu gdje si preuzeo fajlove:
$a = (Get-FileHash .\MujoFix-Setup-0.4.0.exe -Algorithm SHA256).Hash.ToLower()
$b = ((Select-String .\SHA256SUMS.txt -Pattern "MujoFix-Setup-0.4.0.exe").Line -split '\s+')[0]
$a -eq $b   # mora vratiti True
</pre></li>
  <li><b>Pokreni <code>MujoFix-Setup-0.4.0.exe</code>.</b> Instalira se u <code>%LOCALAPPDATA%\MujoFix</code>, <b>bez administratorskih prava</b> (samo za trenutnog korisnika).</li>
  <li><b>SmartScreen upozorenje je očekivano</b> — build još nije potpisan. Klikni <i>More info</i> → <i>Run anyway</i>.</li>
  <li>Prečica ide u Start meni; <b>desktop ikona je opciona</b> (kućica u instalaciji, isključena po defaultu).</li>
  <li><b>Tiha instalacija</b> (npr. više računara): <code>MujoFix-Setup-0.4.0.exe /SILENT</code> (ili <code>/VERYSILENT</code>).</li>
  <li><b>Deinstalacija:</b> Apps &amp; features → MujoFix. Uklanja i ugrađenu OpenCode kopiju i podatke aplikacije (<code>%LOCALAPPDATA%\MujoFix</code>).</li>
</ol>

<p><b>Ažuriranje:</b> <code>MujoFixCLI.exe update</code> provjeri ima li nova verzija; <code>update --apply</code> preuzme, provjeri sha256 i pokrene instalater. U GUI-ju isto radi dugme <i>Provjeri ažuriranja</i>.</p>

<p><b>Zahtjevi:</b> Windows 10/11 (64-bit). <b>Nema Node ni Python</b> — OpenCode je ugrađen i pinovan na tačnu verziju.</p>

<p><i>netestirano:</i> instalater se kompajlira u CI na svakom push-u, ali njegovo izvršavanje na čistom Win10/Win11 VM-u je još u toku (<a href="https://github.com/xnet-ba/mujofix/issues/1">Issue #1</a>).</p>

### Pokretanje (za developere)

```bash
# Skeniranje (engine radi i iz CLI-ja)
PYTHONPATH=mujofix python3 -m mujofix.cli scan --summary

# Provjera ažuriranja (--apply preuzme, provjeri sha256 i pokrene; Windows)
PYTHONPATH=mujofix python3 -m mujofix.cli update

# Faza 0 SPIKE (opciono, uz živi model)
python3 scripts/phase0_spike.py --model <provider/model>

# Dokaz akcija na pravom Windowsu (apply -> verify -> rollback)
python3 scripts/host_proof.py
```

---

## <h2>⚠️ Disclaimer</h2>

<p><b>Ovaj alat mijenja sistemske postavke računara i dolazi BEZ IKAKVE GARANCIJE.</b> Prije korištenja se preporučuje backup važnih podataka. Promjene se mogu poništiti samo u okviru ugrađenog rollback-a (snapshot po akciji + karantin 30 dana) — System Restore Point nije implementiran, a oporavak izvan rollback-a nije zagarantovan. Ništa u ovoj aplikaciji nije "100% sigurno".</p>

---

<div align="center">
<sub>MujoFix je open source (MIT). Treće strane i licence: <a href="THIRD_PARTY_NOTICES.md">THIRD_PARTY_NOTICES.md</a>.</sub>
</div>
