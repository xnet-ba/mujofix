<div align="center">

# 🛠️ MujoFix

### AI mehaničar za Windows računar

**Klikneš SCAN — aplikacija nađe probleme, prevede ih u običan jezik, predloži plan popravki, ti odobriš, ona popravi, provjeri i vrati nazad ako nešto pođe po zlu.**

[![Status](https://img.shields.io/badge/status-Faza_1-blue)](docs/STATUS.md)
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

> <p><b>"Tvoj računar ima 7 problema.<br>🔴 2 ozbiljna &nbsp; 🟠 3 srednja &nbsp; 🟢 2 mala"</b></p>

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
  <li><b>SCAN</b> — paralelni moduli skeniranja s progres barom i mogućnošću otkazivanja.</li>
  <li><b>ANALIZA</b> — svaki nalaz ima ozbiljnost (<code>CRITICAL / MEDIUM / LOW</code>), procjenu uticaja, rizik popravke i oznaku da li je popravka reverzibilna.</li>
  <li><b>PRIKAZ</b> — jednostavan sažetak običnim jezikom + proširiva lista detalja.</li>
  <li><b>PLAN</b> — AI sastavi plan popravki (koraci, redoslijed, procjena vremena i rizika). Korisnik odobrava: <b>sve, pojedinačno ili ništa. Bez odobrenja se NIŠTA ne mijenja.</b></li>
  <li><b>IZVRŠENJE</b> — prije svakog koraka snapshot/rollback tačka, pa izvršenje.</li>
  <li><b>VERIFIKACIJA</b> — nakon svakog koraka ponovo se izmjeri isto što je nalaz detektovao i potvrdi da je problem stvarno riješen.</li>
  <li><b>ROLLBACK</b> — ako verifikacija padne ili se stanje pogorša, korak se <b>automatski vraća</b> i korisnik se izvijesti.</li>
  <li><b>IZVJEŠTAJ</b> — prije/poslije (oslobođeni GB, vrijeme boot-a, broj startup stavki) + opcija <b>"Poništi sve"</b>.</li>
</ol>

<details>
<summary><b>Zašto svaki nalaz mora imati dokaz?</b></summary>
<p>AI smije govoriti <b>samo o podacima koje je scanner stvarno prikupio</b> (sirova mjerenja, ključevi registra, event ID-jevi, putanje). Bez dokaza nalaz se ne prikazuje. Kad je AI nesiguran, mora to izričito reći. Zabranjeno: izmišljeni procenti, brojke i tvrdnje o uzroku bez dokaza.</p>
</details>

---

## <h2>🧩 Moduli skeniranja</h2>

<p>Svi moduli su pluginovi s istim interfejsom (<code>scan()</code> nikad ne ruši aplikaciju — greška postaje <i>skipped</i> izvještaj). Svaki modul provjerava verziju Windowsa i graceful se isključuje gdje nije podržan.</p>

<table>
  <tr><th>Modul</th><th>Šta gleda</th><th>Faza</th></tr>
  <tr><td>⚡ Performanse</td><td>CPU/RAM/disk po procesu, boot vrijeme (Event Log)</td><td>5</td></tr>
  <tr><td>🚀 Startup</td><td>Run/RunOnce ključevi, Startup folder, Taskovi, auto-servisi</td><td>1 ✅</td></tr>
  <tr><td>🔁 Servisi</td><td>Servisi koji se ruše (Event ID 7031/7034), neočekivana stanja</td><td>1 ✅</td></tr>
  <tr><td>💾 Disk</td><td>Slobodan prostor, temp, WU keš, recycle bin, Windows.old, SMART</td><td>1 ✅</td></tr>
  <tr><td>📁 Veliki fajlovi i duplikati</td><td>Veličina → djelimični hash → puni hash; duplikati se <b>nikad ne brišu automatski</b></td><td>5</td></tr>
  <tr><td>🔧 Drajveri i paketi</td><td>Stari drajveri (pnputil), zaostali instaleri, nekorišteni programi</td><td>5</td></tr>
  <tr><td>⚙️ Konfiguracija</td><td>PATH, env varijable, hosts, power plan, SFC/DISM indikatori</td><td>5</td></tr>
  <tr><td>🌐 Mreža</td><td>DNS, proxy, adapteri, latencija, hosts hijack, Winsock</td><td>5</td></tr>
  <tr><td>🕵️ Sumnjivi procesi</td><td>Nepotpisani procesi na čudnim lokacijama, autostart iz Temp-a. <b>Ne tvrdi "virus"</b> — kaže "sumnjivo, razlozi: …"</td><td>5</td></tr>
  <tr><td>🔒 Permisije</td><td>Preširoke ACL dozvole, svijet-zapisivi folderi u PATH-u, UAC, share-ovi</td><td>5</td></tr>
</table>

---

## <h2>🤖 AI sloj</h2>

<p>MujoFix koristi <b>OpenCode</b> (pinovana, testirana verzija, MIT licenca) kao AI motor — instalira se zajedno s aplikacijom, korisnik ne instalira ništa ručno (ni Node ni npm).</p>

<pre>
MujoFix UI → MujoFix Core (scanneri, katalog, executor, rollback)
                    │
                    └── OpenCode child proces (samo 127.0.0.1, slučajna lozinka)
                              │
                              └── MujoFix MCP server (samo 5 alata, svi read-only + validator)
</pre>

<ul>
  <li><b>Izvršenje je ISKLJUČIVO u Coreu.</b> OpenCode objašnjava i predlaže, validator provjerava (JSON schema + allowlista), korisnik odobrava, deterministički executor izvršava. OpenCode nikad ne izvršava komande.</li>
  <li>Agent <code>mujofix</code>: <b>svi ugrađeni alati zabranjeni</b> (bash, edit, write, web…), dozvoljeni samo MujoFix MCP alati, deny po defaultu.</li>
  <li><b>Fallback lanac:</b> model A → B → C → <b>OFFLINE mod</b> (predefinisana objašnjenja bez AI-ja).</li>
  <li><b>Privatnost:</b> prije prvog korištenja AI-ja — ekran pristanka (koji podaci idu, kome, primjer payload-a). Anonimizacija prije slanja; default je offline dok korisnik ne pristane.</li>
</ul>

---

## <h2>🛡️ Sigurnost i povratak stanja</h2>

<ul>
  <li><b>Zaštićene zone</b> (hard-coded blacklist): System32, WinSxS, Program Files (osim kroz uninstaller), korisnički dokumenti/slike/desktop, boot konfiguracija, BitLocker, Defender (samo čitanje).</li>
  <li><b>Prije popravke:</b> System Restore Point gdje je dozvoljen + vlastiti manifest: export registry ključeva, <b>karantin fajlova</b> (ne trajno brisanje, rok 30 dana), čuvanje stanja servisa/taskova.</li>
  <li><b>Svaka akcija:</b> precondition → snapshot → apply → verify → rollback ako zatreba. Akcija bez <code>rollback()</code> ne smije biti auto-fix.</li>
  <li><b>Dry-run mod</b>, kompletan <b>audit log</b> (JSON + čitljiv prikaz).</li>
  <li><b>Nikad:</b> gašenje antivirusa/firewalla/Windows Update-a, mijenjanje zaštitnih politika.</li>
</ul>

---

## <h2>🚦 Status projekta</h2>

<table>
  <tr><th>Faza</th><th>Sadržaj</th><th>Stanje</th></tr>
  <tr><td><b>0 — SPIKE</b></td><td>Dokaz: bundlovani OpenCode kao child, besplatni modeli, MCP alat, zabrana shell-a, offline</td><td>🟡 kod gotov, čeka Win VM</td></tr>
  <tr><td><b>1</b></td><td>Skeleton + CLI scanner (startup, disk, servisi) + model nalaza</td><td>🟢 gotovo (Linux dokazi)</td></tr>
  <tr><td><b>2</b></td><td>Action katalog + runner (snapshot/verify/rollback)</td><td>🔵 u radu</td></tr>
  <tr><td><b>3</b></td><td>GUI (sažetak, plan, odobravanje, progres, izvještaj)</td><td>⚪ planirano</td></tr>
  <tr><td><b>4</b></td><td>Puni AI sloj (MCP, validator, fallback, pristanak, offline)</td><td>⚪ planirano</td></tr>
  <tr><td><b>5</b></td><td>Preostali moduli (mreža, drajveri, duplikati, procesi, permisije…)</td><td>⚪ planirano</td></tr>
  <tr><td><b>6</b></td><td>Installer, potpisivanje, auto-update, javni release</td><td>⚪ planirano</td></tr>
</table>

<p>Detalji po sesiji: <a href="docs/STATUS.md">docs/STATUS.md</a> • Pravila za kodere: <a href="AGENTS.md">AGENTS.md</a></p>

### Pokretanje (za developere, trenutno)

```bash
# Skeniranje (engine radi i iz CLI-ja)
PYTHONPATH=mujofix python3 -m mujofix.cli scan --summary

# Faza 0 SPIKE (na Win10/Win11 VM-u, uz Zen model)
python3 scripts/phase0_spike.py --model <provider/model>

# Testovi
python3 -m unittest discover -s mujofix/tests
```

---

## <h2>⚠️ Disclaimer</h2>

<p><b>Ovaj alat mijenja sistemske postavke računara i dolazi BEZ IKAKVE GARANCIJE.</b> Prije korištenja se preporučuje backup važnih podataka. Promjene se mogu poništiti samo u okviru ugrađenog rollback-a (karantin 30 dana, restore point) — oporavak izvan toga nije zagarantovan. Ništa u ovoj aplikaciji nije "100% sigurno".</p>

---

<div align="center">
<sub>MujoFix je open source (MIT). Treće strane i licence: <a href="THIRD_PARTY_NOTICES.md">THIRD_PARTY_NOTICES.md</a> (u izradi).</sub>
</div>
