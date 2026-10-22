"""i18n niske: default bs (hr/sr), struktura spremna za en."""

STRINGS = {
    "bs": {
        "app_title": "MujoFix — AI mehaničar za Windows",
        "intro": ("MujoFix pregleda računar i predlaže popravke običnim jezikom. "
                  "Ništa se ne mijenja bez tvog odobrenja."),
        "scan": "SCAN",
        "cancel": "Zaustavi",
        "fix_all": "POPRAVI SVE",
        "select_all": "Sve",
        "select_none": "Ništa",
        "show_tech": "Prikaži tehničke detalje",
        "undo_all": "Poništi sve",
        "quarantine_view": "Karantin",
        "quarantine_view_now": "Karantin ({n})",
        "quarantine_title": "MujoFix — karantin",
        "quarantine_info": ("U karantinu: {n} fajlova, {gb}. Fajlovi bez "
                            "poznate originalne putanje se mogu samo "
                            "obrisati."),
        "quarantine_unknown_source": "nepoznata originalna putanja",
        "quarantine_size": "Veličina",
        "quarantine_original": "Originalna putanja",
        "quarantine_restore": "Vrati odabrano",
        "quarantine_delete": "Obriši odabrano",
        "quarantine_restored": "Vraćeno na: {p}",
        "quarantine_restore_failed": "Nije vraćeno: {e}",
        "quarantine_delete_confirm": ("Trajno obrisati {name} ({gb})?\n"
                                      "Ovo se NE može poništiti."),
        "purge_quarantine": "Očisti karantin",
        "purge_quarantine_now": "Očisti karantin ({n} fajlova, {gb})",
        "purge_confirm": ("Trajno obrisati {n} fajlova iz karantina ({gb})?\n"
                          "Ovo se NE može poništiti (fajlovi su već izvan "
                          "sistema)."),
        "purge_cancelled": "Čišćenje karantina otkazano — ništa nije obrisano.",
        "quarantine_purged": "Karantin očišćen: {n} fajlova, oslobođeno {gb}.",
        "report_freed": "Oslobođeno: {gb}.",
        "summary_none": "Nema problema. Računar je zdrav.",
        "summary_many": "Tvoj računar ima {n} problema.",
        "sev_line": "🔴 {c} ozbiljna   🟠 {m} srednja   🟢 {l} mala",
        "plan_ai_header": ("AI predlog plana (predlog — primjenjuju se akcije iz odabranih nalaza):"),
        "no_autofix": "nema automatske popravke u ovoj fazi (samo preporuka)",
        "uac_note": ("Treba admin dozvolu — pokreni MujoFix kao administrator "
                     "pa ponovi: {a}"),
        "elevate_button": "Pokreni kao administrator",
        "elevate_started": ("Zatražena je admin dozvola. Ako je prihvatiš, "
                            "MujoFix se otvara u novom prozoru — skeniraj i "
                            "popravi ponovo."),
        "elevate_denied": "Elevacija odbijena ili nije uspjela.",
        "update_button": "Provjeri ažuriranja",
        "update_checking": "Provjeravam ažuriranja...",
        "update_uptodate": "Imaš najnoviju verziju ({v}).",
        "update_available": ("Dostupna je nova verzija {v} ({f}). "
                             "Preuzeti i pokrenuti instalaciju?"),
        "update_done": ("Preuzeto: {p}. Ako se otvorio instalater, prati "
                        "njegove korake. Aplikacija se zatvara."),
        "update_failed": "Ažuriranje nije uspjelo: {e}",
        "report_ok": "Popravljeno: {ok}, preskočeno: {skip}, palo: {fail}.",
        "theme": "Tamna tema",
        "explain_ai": "Objasni nalaze (AI)",
        "sent_log": "Šta je poslano AI-ju",
        "log_scanning": "scan...",
        "log_ai_declined": "AI odbijen — ostajem u offline modu.",
        "log_ai_explaining": "Objašnjavam — AI radi u pozadini…",
        "log_ai_failed": "AI nije uspio: {m}",
        "fix_stopped": "zaustavljeno, vraćam tekući korak po runneru",
        "dry_run_label": "Probni mod (ništa se ne mijenja)",
        "report_dry": ("Probni mod: {ok} koraka bi se izvršilo, {skip} preskočeno, {fail} ne bi prošlo — ništa nije promijenjeno."),
        "undo_one": "poništeno: {a}",
        "undo_failed": "PONIŠTAVANJE PALO {a}: {e}",
        "consent_title": "MujoFix — pristanak za AI",
        "consent_intro": ("AI objašnjenja znače da podaci o tvom računaru "
                          "napuštaju računar. Bez pristanka aplikacija radi u "
                          "offline modu."),
        "consent_current_on": "AI je trenutno UKLJUČEN.",
        "consent_current_off": "AI je trenutno ISKLJUČEN (offline mod).",
        "consent_example_label": ("Ovaj tačan tekst ide modelu (nalazi su "
                                  "anonimizirani):"),
        "consent_remember": "Zapamti izbor",
        "consent_accept": "Prihvatam AI",
        "consent_reject": "Ostajem offline",
        "sent_log_title": "MujoFix — šta je poslano AI-ju",
        "ai_none": "Nema nalaza. Računar je zdrav.",
        "ai_offline_title": "[OFFLINE, bez AI-ja] {title} (ozbiljnost: {sev})",
        "ai_offline_unknown": "nepoznat nalaz",
        "ai_offline_why": "Zašto: {v}",
        "ai_offline_impact": "Uticaj: {v}",
        "ai_offline_risk": "Rizik popravke: {v} (može se poništiti: {rev})",
        "ai_offline_evidence": "Dokaz: {v}",
        "ai_offline_no_evidence": "scanner nije priložio dodatne podatke",
        "ai_offline_tech": "Tehnički detalji: {v}",
        "ai_offline_action": ("Aplikacija može: {v} — pokreni kroz odobrenje "
                               "u \"Popravi sve\"."),
        "ai_offline_no_action": ("Za ovaj nalaz nema automatske popravke u "
                                 "katalogu akcija."),
        "ai_offline_footer": ("Ovo objašnjenje je sastavljeno isključivo iz "
                              "podataka koje je scanner prikupio (bez AI-ja); "
                              "nema dodatnih pretpostavki."),
        "ai_yes": "da",
        "ai_no": "ne",
        "ai_note_no_consent": "offline: pristanak nije dat",
        "ai_note_no_binary": "offline: nema OpenCode binary-ja ({e})",
        "ai_note_unavailable": "offline: živi model nedostupan ({e})",
        "ai_note_no_free_model": "offline: nema besplatnog Zen modela",
        "ai_note_live": "živi model: {m}",
        "sc_startup_title": "{n} programa se pali s Windowsom",
        "sc_startup_why": ("Programi koji se pale s sistemom produžuju "
                           "prijavu i troše memoriju u pozadini. Broj "
                           "stavki je orijentir — nije izmjereno stvarno "
                           "vrijeme boot-a."),
        "sc_startup_impact_many": "sporija prijava i {n} pozadinskih programa",
        "sc_startup_impact_few": "blago usporenje prijave",
        "sc_startup_risk": ("nizak: onemogućavanje stavke se poništava jednim "
                            "klikom"),
        "sc_startup_tech": "Run/RunOnce ključevi + Startup folderi",
        "sc_startup_unavailable": "startup skeniranje radi samo na Windowsu",
        "sc_services_title": "{n} automatskih servisa ne radi",
        "sc_services_why": ("Servis podešen na automatski start bi morao "
                            "raditi nakon boot-a. Zaustavljen automatski "
                            "servis znači rušenje ili pogrešnu "
                            "konfiguraciju."),
        "sc_services_impact": ("funkcije tih servisa ne rade (mreža, štampanje, "
                               "update...)"),
        "sc_services_risk": ("srednji: restart servisa je reverzibilan, ali "
                             "uzrok rušenja može ostati"),
        "sc_services_unavailable": "servisi postoje samo na Windowsu",
        "sc_common_unknown": "nepoznato",
        "sc_config_path_writable_title": ("{n} foldera u PATH-u može "
                                          "mijenjati svako"),
        "sc_config_path_writable_why": ("Svijet-zapisiv folder u PATH-u "
                                        "znači da bilo koji program može "
                                        "podmetnuti lažni .exe koji ćeš "
                                        "slučajno pokrenuti."),
        "sc_config_path_writable_impact": "rizik podmetanja programa",
        "sc_config_path_writable_risk": ("srednji: skidanje prava pisanja "
                                         "traži oprez"),
        "sc_config_path_writable_tech": ("stat S_IWOTH nad PATH stavkama "
                                         "(samo POSIX)"),
        "sc_config_path_missing_title": "{n} PATH stavki ne postoji",
        "sc_config_path_missing_why": ("Mrtve stavke u PATH-u usporavaju "
                                       "traženje programa i lome skripte "
                                       "koje računaju na njih."),
        "sc_config_path_missing_impact": "sporije pokretanje komandi",
        "sc_config_path_missing_risk": "nizak: čišćenje je reverzibilno",
        "sc_config_path_missing_tech": "os.path.isdir nad PATH stavkama",
        "sc_config_temp_title": "Varijabla {var} ne pokazuje na ispravan folder",
        "sc_config_temp_why": ("Programi pišu privremene fajlove u TEMP; "
                               "loša putanja ruši instalere i snimanja."),
        "sc_config_temp_impact": "rušenje instalera/programa",
        "sc_config_temp_risk": "nizak: postavljanje putanje je reverzibilno",
        "sc_config_temp_tech": "os.environ + isdir",
        "sc_config_power_title": "Aktivan je štedljivi plan napajanja",
        "sc_config_power_why": ("Power Saver smanjuje performanse da uštedi "
                                "struju — na desktopu je to često čista "
                                "šteta."),
        "sc_config_power_impact": "smanjene performanse",
        "sc_config_power_risk": "nizak: promjena plana je reverzibilna",
        "sc_config_sfc_title": "SFC tragovi: {n} grešaka u CBS logu",
        "sc_config_sfc_why": ("Servisiranje komponenti prijavljuje neuspjehe "
                              "— moguća oštećena sistemska datoteka "
                              "(provjera: sfc /scannow)."),
        "sc_config_sfc_impact": "moguća nestabilnost sistema",
        "sc_config_sfc_risk": "nizak: samo čitamo log, ne mijenjamo ništa",
        "sc_config_power_tech": "powercfg /getactivescheme",
        "sc_config_sfc_tech": "rep CBS.log ({n} B)",
        "sc_drivers_title": "{n} drajvera starijih od {years} godina",
        "sc_drivers_why": ("Zastarjeli drajveri znaju rušiti sistem nakon "
                           "updatea Windowsa; noviji donose ispravke "
                           "stabilnosti."),
        "sc_drivers_impact": "moguća nestabilnost/plavi ekran",
        "sc_drivers_risk": ("srednji: update drajvera traži restart; rollback "
                            "kroz Device Manager"),
        "sc_drivers_tech": ("pnputil /enum-drivers. Nekorištene programe ne "
                            "prijavljujemo: Windows ne mjeri korištenje po "
                            "programu."),
        "sc_drivers_unavailable": "pnputil postoji samo na Windowsu",
        "sc_duplicates_title": "{n} grupa duplikata (~{mb} MB viška)",
        "sc_duplicates_why": ("Iste velike datoteke na više mjesta jedu disk. "
                              "Potvrđene kopije idu u karantin (jedna "
                              "ostaje) — ništa se ne briše, rollback vraća "
                              "sve."),
        "sc_duplicates_impact": "moguće oslobađanje ~{mb} MB (karantin)",
        "sc_duplicates_risk": ("srednji: prva kopija ostaje, ostale u karantin; "
                               "rollback vraća"),
        "sc_duplicates_tech": "veličina -> sha256(64KB) -> puni sha256",
        "sc_net_dns_title": "Internet imena se ne razrješavaju (DNS ne radi)",
        "sc_net_dns_why": ("Bez DNS-a ne otvara se nijedna stranica ni "
                           "servis; uzrok je obično ruter, DNS server ili "
                           "hosts fajl."),
        "sc_net_dns_impact": "nema pristupa internetu imenima",
        "sc_net_unreachable_title": "DNS radi, ali nema veze do internet servisa",
        "sc_net_unreachable_why": ("Imena se razrješavaju, ali TCP veza do "
                                   "javnih servera ne uspijeva — moguć "
                                   "firewall, proxy ili prekid kod "
                                   "provajdera."),
        "sc_net_unreachable_impact": "internet praktično ne radi",
        "sc_net_slow_title": "Veza do interneta je spora ({ms} ms)",
        "sc_net_slow_why": ("TCP handshake preko sekunde znači zagušenje, "
                            "loš WiFi ili problem kod provajdera. Mjereno "
                            "ka javnom DNS-u."),
        "sc_net_slow_impact": "sporo učitavanje svega",
        "sc_net_hosts_title": "Sumnjivi zapisi u hosts fajlu ({n})",
        "sc_net_hosts_why": ("Hosts fajl preusmjerava poznate domene mimo "
                             "DNS-a — klasična tehnika otmice prometa. "
                             "Provjeri da li si ih sam dodao."),
        "sc_net_hosts_impact": "moguće preusmjeravanje na lažno",
        "sc_net_hosts_risk": "nizak: uklanjanje zapisa je reverzibilno",
        "sc_net_proxy_title": "Uključen je proxy za internet promet",
        "sc_net_proxy_why": ("Proxy može usporavati i nadgledati promet. Ako "
                             "ga nisi sam uključio (firma, VPN), vrijedi "
                             "provjeriti."),
        "sc_net_proxy_impact": "moguće usporenje/nadzor prometa",
        "sc_net_proxy_risk": "nizak: isključivanje je reverzibilno",
        "sc_net_proxy_set": "postavljen",
        "sc_net_winsock_title": "Winsock katalog se ne može pročitati",
        "sc_net_winsock_why": ("Oštećen mrežni stek zna rušiti veze svim "
                               "programima; popravka je `netsh winsock "
                               "reset` + restart."),
        "sc_net_winsock_impact": "mogući prekidi veza",
        "sc_net_winsock_risk": "srednji: reset traži restart",
        "sc_net_check_risk": "nizak: provjera ne mijenja ništa",
        "sc_perm_uac_title": "UAC (kontrola korisničkih naloga) je isključen",
        "sc_perm_uac_why": ("Bez UAC-a svaki program tiho dobija admin prava "
                            "— najjači sigurnosni mehanizam Windowsa ne "
                            "radi."),
        "sc_perm_uac_impact": "bilo koji program može mijenjati sistem",
        "sc_perm_uac_risk": "nizak: uključivanje je reverzibilno (uz UAC prompt)",
        "sc_perm_acl_title": "Preširoke dozvole na sistemskim folderima",
        "sc_perm_acl_why": ("Obični korisnici (ili Everyone) mogu pisati po "
                            "sistemskim folderima — podmetanje "
                            "malware-a."),
        "sc_perm_acl_impact": "moguće trajno kompromitovanje sistema",
        "sc_perm_acl_risk": "srednji: zatezanje ACL-a traži oprez",
        "sc_perm_shares_title": "{n} nedefaultnih dijeljenih foldera",
        "sc_perm_shares_why": ("Svaki share je ulaz u računar s mreže; "
                               "provjeri da li su namjerni i kome su "
                               "dostupni."),
        "sc_perm_shares_impact": "mogući ulaz s mreže",
        "sc_perm_shares_risk": "nizak: gašenje sharea je reverzibilno",
        "sc_perm_path_title": "Svijet-zapisivi folderi u PATH-u",
        "sc_perm_path_why": "Isto kao Windows verzija: podmetanje programa.",
        "sc_perm_path_impact": "rizik podmetanja programa",
        "sc_perm_path_risk": "nizak: skidanje prava je reverzibilno",
        "sc_susp_title": "{n} sumnjivih procesa (ne tvrdimo da je virus)",
        "sc_susp_why": ("Proces bez validnog potpisa na neobičnoj lokaciji "
                        "ili autostart iz Temp-a su klasični znaci "
                        "zloupotrebe. Ovo je sumnja na osnovu razloga "
                        "ispod, ne dijagnoza."),
        "sc_susp_impact": "moguća zloupotreba sistema",
        "sc_susp_risk": "nizak: samo prijavljujemo, ništa ne gasimo automatski",
        "sc_susp_defender_title": "Defender real-time zaštita je isključena",
        "sc_susp_defender_why": ("Bez real-time zaštite sistem je otvoren za "
                                 "poznate prijetnje. MujoFix ovo nikad sam "
                                 "ne mijenja — samo javlja da provjeriš."),
        "sc_susp_defender_impact": "bez aktivne antivirus zaštite",
        "sc_susp_defender_risk": "nema: samo čitamo status",
        "sc_susp_unavailable": "lista procesa i potpisi čitaju se samo na Windowsu",
        "sc_unavailable_generic": "modul nije podržan na ovoj platformi",
        "sc_error": "greška scannera ({kind}): {e}",
        "act_apply_failed": "apply pao, vraceno: {e}",
        "act_cancelled": "otkazano",
        "act_clean_temp_description": "Selimo stare privremene fajlove u karantin (30 dana).",
        "act_clean_temp_risk": "nizak: karantin, ne trajno brisanje; rollback vraca sve",
        "act_disable_proxy_description": "Iskljucujemo proxy za internet promet (vracamo po potrebi).",
        "act_disable_proxy_risk": "nizak: cuvamo ProxyEnable, rollback ga vraca",
        "act_disable_startup_item_description": "Onemogucavamo program da se sam pali s Windowsom.",
        "act_disable_startup_item_risk": "nizak: vrijednost se cuva i vraca jednim rollback-om",
        "act_dry_run": "dry-run, nista nije mijenjano: {r}",
        "act_dup_done": "u karantin premjesteno {n} kopija",
        "act_dup_left": "{n} kopija je ostalo na mjestu",
        "act_dup_lost": "izgubljena i zadrzana kopija: {p}",
        "act_dup_none": "nema potvrdjenih duplikata za karantin",
        "act_dup_ready": "{n} suvisnih kopija u karantin",
        "act_env_already_ok": "{v} je vec ispravan ({cur})",
        "act_env_dead_entry": "mrtvi unos u {h}: {e}",
        "act_env_empty": "prazan unos",
        "act_env_fixed": "{v} pokazuje na ispravan folder",
        "act_env_not_in_path": "unos '{e}' nije u PATH-u (vec ocisceno?)",
        "act_env_path_unreadable": "PATH se ne moze procitati posle izmjene",
        "act_env_removed": "mrtvi unos uklonjen",
        "act_env_still_in_path": "unos {e} je i dalje u PATH-u",
        "act_env_still_wrong": "{v} i dalje nije ispravan ({cur})",
        "act_env_target": "{v} -> {t}",
        "act_env_unknown_var": "nepoznata varijabla: {v}",
        "act_fix_temp_var_description": "Vracamo TEMP/TMP na ispravan privremeni folder.",
        "act_fix_temp_var_risk": "nizak: stara vrijednost se cuva, rollback vraca tacno",
        "act_precondition_failed": "precondition pao: {r}",
        "act_proxy_done": "proxy iskljucen",
        "act_proxy_not_on": "proxy nije ukljucen (ProxyEnable != 1)",
        "act_proxy_on": "proxy je ukljucen, iskljucujemo ga",
        "act_proxy_still_on": "proxy je i dalje ukljucen (ProxyEnable={e})",
        "act_quarantine_duplicates_description": "Visak identicnih kopija selimo u karantin (jedna ostaje).",
        "act_quarantine_duplicates_risk": "srednji: prva kopija ostaje, ostale u karantin; rollback vraca sve",
        "act_remove_path_entry_description": "Uklanjamo mrtvi unos iz PATH varijable.",
        "act_remove_path_entry_risk": "nizak: stara vrijednost se cuva, rollback vraca tacno",
        "act_restart_service_description": "Gasimo pa palimo servis koji je stao.",
        "act_restart_service_risk": "srednji: kratki prekid funkcije servisa; ako se opet srusi, verify pada i stanje se vraca",
        "act_snapshot_failed": "snapshot pao: {e}",
        "act_startup_disabled": "{e} vise nije u startup-u",
        "act_startup_exists": "stavka postoji: {v}",
        "act_startup_gone": "stavka nestala izmedju precondition i snapshot",
        "act_startup_missing": "stavka {e} ne postoji (vec onemogucena?)",
        "act_startup_still": "{e} je i dalje prisutna",
        "act_svc_exists": "servis {s} postoji (stanje: {state})",
        "act_svc_gone": "servis {s} nestao",
        "act_svc_missing": "servis {s} ne postoji",
        "act_svc_running": "{s} radi",
        "act_svc_start_failed": "start pao: {e}",
        "act_svc_state": "{s} stanje: {now}",
        "act_temp_done": "ocisceno {n} fajlova",
        "act_temp_left": "ostalo {n} fajlova na mjestu",
        "act_temp_no_dir": "folder ne postoji: {d}",
        "act_temp_none": "nema fajlova starijih od {days} dana",
        "act_temp_ready": "{n} fajlova za karantin",
        "act_verify_failed": "verifikacija pala, vraceno: {d}",
        "act_win_only": "samo Windows",
        "vp_no_steps": "plan mora imati nepraznu listu 'steps'",
        "vp_no_target": "korak {i}: nedostaje 'target'",
        "vp_not_object": "plan mora biti JSON objekat",
        "vp_ok": "prihvaceno {n} koraka",
        "vp_protected": "korak {i}: zasticena zona '{p}'",
        "vp_step_not_object": "korak {i} nije objekat",
        "vp_too_many": "previse koraka ({n} > {max})",
        "vp_unknown_action": "korak {i}: akcija '{a}' nije u katalogu ({allowed})",
        "up_bad_version": "neispravna verzija: {v}",
        "up_download_failed": "preuzimanje palo: {e}",
        "up_no_asset": "nema fajla za preuzimanje",
        "up_sha_mismatch": "sha256 se ne poklapa — fajl odbacen",
        "up_unreachable": "ne mogu doci do {u}: {e}",
        "cli_unknown_scanner": "nepoznat scanner '{n}'",
        "cli_update_available": "Nova verzija: {new} (imam {cur}).",
        "cli_update_check_failed": "Provjera update-a nije uspjela: {e}",
        "cli_update_failed": "Update nije uspio: {e}",
        "cli_update_uptodate": "Verzija {v} je najnovija.",
        "act_proxy_changed": "proxy stanje se promijenilo prije snapshota",
        "act_env_path_gone": "PATH nestao izmedju precondition i snapshota",
        "act_hosts_changed": "hosts fajl se promijenio vise nego sto je planirano",
        "act_hosts_done": "uklonjeno {n} zapisa ({ip} {host})",
        "act_hosts_gone": "zapis {ip} {host} je nestao prije snapshota",
        "act_hosts_no_file": "hosts fajl ne postoji: {p}",
        "act_hosts_not_found": "zapis {ip} {host} nije u hosts fajlu",
        "act_hosts_ready": "zapis {ip} {host} je u hosts fajlu",
        "act_hosts_still": "zapis {ip} {host} je i dalje u hosts fajlu",
        "act_hosts_unreadable": "hosts fajl se ne moze procitati: {e}",
        "act_remove_hosts_entry_description": "Uklanjamo sumnjiv zapis iz hosts fajla (vracamo po potrebi).",
        "act_remove_hosts_entry_risk": "srednji: hosts je zastita DNS-a; snapshot cuva cijeli fajl, rollback ga vraca",
        "act_disable_power_saver_description": "Vracamo plan napajanja na uravnotezeni (Balanced).",
        "act_disable_power_saver_risk": "nizak: mijenja se samo aktivni plan; snapshot pamti stari GUID i rollback ga vraca",
        "act_power_already": "plan napajanja je vec uravnotezen (Balanced)",
        "act_power_done": "plan napajanja je sada uravnotezen (Balanced)",
        "act_power_gone": "aktivni plan se promijenio prije snapshota",
        "act_power_ready": "aktivan je drugi plan ({guid}), prebacujemo na Balanced",
        "act_power_still": "plan napajanja nije promijenjen (aktivan: {guid})",
        "act_power_unreadable": "aktivni plan napajanja se ne moze procitati: {e}",
        "act_remove_share_description": "Uklanjamo mrezni share koji nisi namjerno napravio (vracamo po potrebi).",
        "act_remove_share_risk": "srednji: share se zatvara s mreze; snapshot pamti putanju i rollback ga vraca",
        "act_share_default": "share {n} je sistemski (administrativni) — ne diramo ga",
        "act_share_done": "share {n} je uklonjen s mreze",
        "act_share_gone": "share {n} je nestao prije snapshota",
        "act_share_missing": "share {n} ne postoji",
        "act_share_ready": "share {n} vodi na {p}",
        "act_share_still": "share {n} je i dalje prisutan",
        "act_share_unreadable": "share se ne moze procitati: {e}",
        "sc_disk_almost_full_title": "Disk je gotovo pun (ostalo {gb} GB)",
        "sc_disk_almost_full_why": ("Kad ponestane slobodnog prostora, Windows "
                                   "usporava, updatei pucaju, a programi se "
                                   "ruše pri snimanju."),
        "sc_disk_almost_full_impact": ("rizik rušenja programa i neuspjelih "
                                       "updatea"),
        "sc_disk_temp_cache_risk": ("nizak: brišemo samo temp i keš koji se sam "
                                    "obnavlja"),
        "sc_disk_low_title": "Malo slobodnog prostora ({gb} GB)",
        "sc_disk_low_why": ("Ispod 20% slobodno, vrijeme je za čišćenje prije "
                            "nego postane kritično."),
        "sc_disk_low_impact": "usporenje i rizik punog diska",
        "sc_disk_temp_title": "Privremeni fajlovi zauzimaju {gb} GB",
        "sc_disk_temp_why": ("Temp se sam ne čisti; stari instalacioni ostaci i "
                             "keš mogu narasti do više gigabajta."),
        "sc_disk_temp_impact": "oslobađa se ~{gb} GB",
        "sc_disk_temp_risk": ("nizak: brišu se fajlovi stariji od 7 dana, "
                              "karantin 30 dana"),
        "sc_disk_wu_title": "Windows Update keš zauzima {gb} GB",
        "sc_disk_wu_why": ("Preuzeti update paketi ostaju na disku i nakon "
                           "instalacije."),
        "sc_disk_wu_impact": "oslobađa se ~{gb} GB",
        "sc_disk_wu_risk": "nizak: keš se ponovo preuzme ako zatreba",
        "sc_disk_old_title": "Stara instalacija Windowsa ({gb} GB)",
        "sc_disk_old_why": ("Folder Windows.old ostaje nakon nadogradnje; briše "
                            "se sam nakon ~10 dana, ali do tada jede disk."),
        "sc_disk_old_impact": "oslobađa se ~{gb} GB",
        "sc_disk_old_risk": ("srednji: nakon brisanja nema povratka na staru "
                             "verziju"),
        "cli_summary": ("Tvoj računar ima {n} problema.\n"
                         "  {c} ozbiljna  {m} srednja  {l} mala"),
        "summary_fixable": "Automatski se može popraviti: {n}.",
        "summary_no_autofix": "Nijedan nalaz nema automatsku popravku — "
                              "vidi preporuke u nalazima.",
        "ai_settings": "AI: uključi/isključi",
        "audit_saved": "Dnevnik izvršavanja sačuvan: {p}",
        "audit_failed": "Dnevnik nije sačuvan: {e}",
        "lang_label": "Jezik:",
        "lang_restart": "Jezik je sačuvan — primjenjuje se pri sljedećem pokretanju aplikacije.",
        "ai_state_now": "AI: {s}",
        "ai_state_on": "uključen",
        "ai_state_off": "isključen (offline mod)",
        "ai_example_none": ("Još nema nalaza — primjer zahtjeva se pojavi poslije skeniranja."),
    },
    "en": {
        "app_title": "MujoFix — AI mechanic for Windows",
        "intro": ("MujoFix scans your PC and proposes fixes in plain language. "
                  "Nothing changes without your approval."),
        "scan": "SCAN",
        "cancel": "Stop",
        "fix_all": "FIX ALL",
        "select_all": "All",
        "select_none": "None",
        "show_tech": "Show technical details",
        "undo_all": "Undo all",
        "quarantine_view": "Quarantine",
        "quarantine_view_now": "Quarantine ({n})",
        "quarantine_title": "MujoFix — quarantine",
        "quarantine_info": ("In quarantine: {n} files, {gb}. Files with no "
                            "known original path can only be deleted."),
        "quarantine_unknown_source": "unknown original path",
        "quarantine_size": "Size",
        "quarantine_original": "Original path",
        "quarantine_restore": "Restore selected",
        "quarantine_delete": "Delete selected",
        "quarantine_restored": "Restored to: {p}",
        "quarantine_restore_failed": "Not restored: {e}",
        "quarantine_delete_confirm": ("Permanently delete {name} ({gb})?\n"
                                      "This CANNOT be undone."),
        "purge_quarantine": "Clean quarantine",
        "purge_quarantine_now": "Clean quarantine ({n} files, {gb})",
        "purge_confirm": ("Permanently delete {n} files from quarantine ({gb})?\n"
                          "This CANNOT be undone (the files are already "
                          "outside the system)."),
        "purge_cancelled": "Quarantine cleanup cancelled — nothing was deleted.",
        "quarantine_purged": "Quarantine cleaned: {n} files, freed {gb}.",
        "report_freed": "Freed: {gb}.",
        "summary_none": "No issues. Your PC is healthy.",
        "summary_many": "Your PC has {n} issues.",
        "sev_line": "🔴 {c} critical   🟠 {m} medium   🟢 {l} low",
        "no_autofix": "no automatic fix in this phase (recommendation only)",
        "plan_ai_header": ("AI draft plan (a draft — the actions of the selected findings are what gets applied):"),
        "uac_note": ("Needs admin approval — run MujoFix as administrator and "
                     "retry: {a}"),
        "elevate_button": "Run as administrator",
        "elevate_started": ("Admin access requested. If you accept, MujoFix "
                            "reopens in a new window — scan and fix again."),
        "elevate_denied": "Elevation declined or failed.",
        "update_button": "Check for updates",
        "update_checking": "Checking for updates...",
        "update_uptodate": "You have the latest version ({v}).",
        "update_available": ("A new version {v} is available ({f}). "
                             "Download and run the installer?"),
        "update_done": ("Downloaded: {p}. If an installer opened, follow its "
                        "steps. The app is closing."),
        "update_failed": "Update failed: {e}",
        "report_ok": "Fixed: {ok}, skipped: {skip}, failed: {fail}.",
        "theme": "Dark theme",
        "explain_ai": "Explain findings (AI)",
        "sent_log": "What was sent to the AI",
        "log_scanning": "scan...",
        "log_ai_declined": "AI declined — staying in offline mode.",
        "log_ai_explaining": "Explaining — the AI is working in the background…",
        "log_ai_failed": "AI failed: {m}",
        "fix_stopped": "stopped, rolling back the current step",
        "dry_run_label": "Dry run (nothing is changed)",
        "report_dry": ("Dry run: {ok} steps would run, {skip} skipped, {fail} would fail — nothing was changed."),
        "undo_one": "undone: {a}",
        "undo_failed": "UNDO FAILED {a}: {e}",
        "consent_title": "MujoFix — AI consent",
        "consent_intro": ("AI explanations mean data about your computer "
                          "leaves your computer. Without consent the app runs "
                          "in offline mode."),
        "consent_current_on": "AI is currently ON.",
        "consent_current_off": "AI is currently OFF (offline mode).",
        "consent_example_label": ("This exact text goes to the model (findings "
                                  "are anonymized):"),
        "consent_remember": "Remember this choice",
        "consent_accept": "I accept AI",
        "consent_reject": "Stay offline",
        "sent_log_title": "MujoFix — what was sent to the AI",
        "ai_none": "No findings. The computer is healthy.",
        "ai_offline_title": "[OFFLINE, no AI] {title} (severity: {sev})",
        "ai_offline_unknown": "unknown finding",
        "ai_offline_why": "Why: {v}",
        "ai_offline_impact": "Impact: {v}",
        "ai_offline_risk": "Fix risk: {v} (reversible: {rev})",
        "ai_offline_evidence": "Evidence: {v}",
        "ai_offline_no_evidence": "the scanner attached no extra data",
        "ai_offline_tech": "Technical details: {v}",
        "ai_offline_action": ("The app can: {v} — run it through approval in "
                               "\"Fix all\"."),
        "ai_offline_no_action": ("There is no automatic fix in the action "
                                  "catalog for this finding."),
        "ai_offline_footer": ("This explanation is built only from the data "
                               "the scanner collected (no AI); no extra "
                               "assumptions."),
        "ai_yes": "yes",
        "ai_no": "no",
        "ai_note_no_consent": "offline: consent not given",
        "ai_note_no_binary": "offline: no OpenCode binary ({e})",
        "ai_note_unavailable": "offline: live model unavailable ({e})",
        "ai_note_no_free_model": "offline: no free Zen model",
        "ai_note_live": "live model: {m}",
        "sc_startup_title": "{n} programs start with Windows",
        "sc_startup_why": ("Programs that start with the system delay sign-in "
                           "and use memory in the background. The item count "
                           "is an indicator — actual boot time is not "
                           "measured."),
        "sc_startup_impact_many": "slower sign-in and {n} background programs",
        "sc_startup_impact_few": "slightly slower sign-in",
        "sc_startup_risk": ("low: disabling an entry is reverted with one "
                            "click"),
        "sc_startup_tech": "Run/RunOnce keys + Startup folders",
        "sc_startup_unavailable": "startup scanning only works on Windows",
        "sc_services_title": "{n} automatic services are not running",
        "sc_services_why": ("A service set to start automatically should be "
                            "running after boot. A stopped automatic service "
                            "means a crash or a wrong configuration."),
        "sc_services_impact": ("those services do not work (network, printing, "
                               "updates...)"),
        "sc_services_risk": ("medium: restarting a service is reversible, but "
                             "the crash cause may remain"),
        "sc_services_unavailable": "services only exist on Windows",
        "sc_common_unknown": "unknown",
        "sc_config_path_writable_title": "{n} PATH folders are writable by anyone",
        "sc_config_path_writable_why": ("A world-writable PATH folder means any "
                                        "program can drop a fake .exe that you "
                                        "may run by accident."),
        "sc_config_path_writable_impact": "risk of a planted program",
        "sc_config_path_writable_risk": ("medium: removing write rights needs "
                                         "care"),
        "sc_config_path_writable_tech": ("stat S_IWOTH on PATH entries "
                                         "(POSIX only)"),
        "sc_config_path_missing_title": "{n} PATH entries do not exist",
        "sc_config_path_missing_why": ("Dead PATH entries slow down program "
                                       "lookups and break scripts that rely "
                                       "on them."),
        "sc_config_path_missing_impact": "slower command startup",
        "sc_config_path_missing_risk": "low: cleanup is reversible",
        "sc_config_path_missing_tech": "os.path.isdir on PATH entries",
        "sc_config_temp_title": "The {var} variable does not point to a valid folder",
        "sc_config_temp_why": ("Programs write temporary files to TEMP; a bad "
                               "path breaks installers and saves."),
        "sc_config_temp_impact": "installers/programs crashing",
        "sc_config_temp_risk": "low: setting the path is reversible",
        "sc_config_temp_tech": "os.environ + isdir",
        "sc_config_power_title": "A power-saver plan is active",
        "sc_config_power_why": ("Power Saver lowers performance to save "
                                "energy — on a desktop that is usually pure "
                                "loss."),
        "sc_config_power_impact": "reduced performance",
        "sc_config_power_risk": "low: changing the plan is reversible",
        "sc_config_sfc_title": "SFC traces: {n} failures in the CBS log",
        "sc_config_sfc_why": ("Component servicing reports failures — a system "
                              "file may be damaged (check: sfc /scannow)."),
        "sc_config_sfc_impact": "possible system instability",
        "sc_config_sfc_risk": "low: we only read the log, nothing is changed",
        "sc_config_power_tech": "powercfg /getactivescheme",
        "sc_config_sfc_tech": "tail CBS.log ({n} B)",
        "sc_drivers_title": "{n} drivers older than {years} years",
        "sc_drivers_why": ("Outdated drivers can crash Windows after an "
                           "update; newer ones carry stability fixes."),
        "sc_drivers_impact": "possible instability/blue screen",
        "sc_drivers_risk": ("medium: a driver update needs a restart; rollback "
                            "via Device Manager"),
        "sc_drivers_tech": ("pnputil /enum-drivers. We do not report unused "
                            "programs: Windows does not measure usage per "
                            "program."),
        "sc_drivers_unavailable": "pnputil only exists on Windows",
        "sc_duplicates_title": "{n} duplicate groups (~{mb} MB wasted)",
        "sc_duplicates_why": ("The same large files in several places waste "
                              "disk. Confirmed copies go to quarantine (one "
                              "stays) — nothing is deleted, rollback restores "
                              "everything."),
        "sc_duplicates_impact": "about {mb} MB could be freed (quarantine)",
        "sc_duplicates_risk": ("medium: the first copy stays, the rest go to "
                               "quarantine; rollback restores"),
        "sc_duplicates_tech": "size -> sha256(64KB) -> full sha256",
        "sc_net_dns_title": "Internet names do not resolve (DNS is not working)",
        "sc_net_dns_why": ("Without DNS no page or service opens; the cause "
                           "is usually the router, the DNS server or the "
                           "hosts file."),
        "sc_net_dns_impact": "no internet access by name",
        "sc_net_unreachable_title": "DNS works, but there is no connection to internet services",
        "sc_net_unreachable_why": ("Names resolve, but the TCP connection to "
                                   "public servers fails — possible "
                                   "firewall, proxy or provider outage."),
        "sc_net_unreachable_impact": "the internet effectively does not work",
        "sc_net_slow_title": "The internet connection is slow ({ms} ms)",
        "sc_net_slow_why": ("A TCP handshake over one second means "
                            "congestion, bad WiFi or a provider problem. "
                            "Measured against a public DNS."),
        "sc_net_slow_impact": "everything loads slowly",
        "sc_net_hosts_title": "Suspicious hosts file entries ({n})",
        "sc_net_hosts_why": ("The hosts file redirects known domains past "
                             "DNS — a classic traffic hijack technique. "
                             "Check whether you added them yourself."),
        "sc_net_hosts_impact": "possible redirect to a fake address",
        "sc_net_hosts_risk": "low: removing entries is reversible",
        "sc_net_proxy_title": "A proxy is enabled for internet traffic",
        "sc_net_proxy_why": ("A proxy can slow down and monitor traffic. If "
                             "you did not enable it yourself (company, VPN), "
                             "it is worth checking."),
        "sc_net_proxy_impact": "possible slowdown/traffic monitoring",
        "sc_net_proxy_risk": "low: disabling it is reversible",
        "sc_net_proxy_set": "set",
        "sc_net_winsock_title": "The Winsock catalog cannot be read",
        "sc_net_winsock_why": ("A damaged network stack can break connections "
                               "for every program; the fix is `netsh "
                               "winsock reset` + restart."),
        "sc_net_winsock_impact": "possible connection drops",
        "sc_net_winsock_risk": "medium: the reset needs a restart",
        "sc_net_check_risk": "low: the check changes nothing",
        "sc_perm_uac_title": "UAC (user account control) is disabled",
        "sc_perm_uac_why": ("Without UAC every program silently gets admin "
                            "rights — the strongest Windows security "
                            "mechanism is off."),
        "sc_perm_uac_impact": "any program can change the system",
        "sc_perm_uac_risk": "low: enabling it is reversible (with a UAC prompt)",
        "sc_perm_acl_title": "Overly broad permissions on system folders",
        "sc_perm_acl_why": ("Regular users (or Everyone) can write to system "
                            "folders — malware can be planted."),
        "sc_perm_acl_impact": "possible permanent system compromise",
        "sc_perm_acl_risk": "medium: tightening ACLs needs care",
        "sc_perm_shares_title": "{n} non-default shared folders",
        "sc_perm_shares_why": ("Every share is an entry point from the "
                               "network; check whether they are intentional "
                               "and who can reach them."),
        "sc_perm_shares_impact": "possible entry from the network",
        "sc_perm_shares_risk": "low: disabling a share is reversible",
        "sc_perm_path_title": "World-writable folders in PATH",
        "sc_perm_path_why": "Same as the Windows version: program planting.",
        "sc_perm_path_impact": "risk of a planted program",
        "sc_perm_path_risk": "low: removing rights is reversible",
        "sc_susp_title": "{n} suspicious processes (we are not claiming a virus)",
        "sc_susp_why": ("A process without a valid signature in an unusual "
                        "location or an autostart from Temp are classic "
                        "signs of abuse. This is a suspicion based on the "
                        "reasons below, not a diagnosis."),
        "sc_susp_impact": "possible system abuse",
        "sc_susp_risk": "low: we only report, nothing is killed automatically",
        "sc_susp_defender_title": "Defender real-time protection is off",
        "sc_susp_defender_why": ("Without real-time protection the system is "
                                 "open to known threats. MujoFix never "
                                 "changes this itself — it only tells you to "
                                 "check."),
        "sc_susp_defender_impact": "no active antivirus protection",
        "sc_susp_defender_risk": "none: we only read the status",
        "sc_susp_unavailable": "process list and signatures are read only on Windows",
        "sc_unavailable_generic": "module not supported on this platform",
        "sc_error": "scanner error ({kind}): {e}",
        "act_apply_failed": "apply failed, rolled back: {e}",
        "act_cancelled": "cancelled",
        "act_clean_temp_description": "Move old temporary files to quarantine (30 days).",
        "act_clean_temp_risk": "low: quarantine, no permanent delete; rollback restores everything",
        "act_disable_proxy_description": "Disable the internet proxy (restore on request).",
        "act_disable_proxy_risk": "low: we save ProxyEnable, rollback restores it",
        "act_disable_startup_item_description": "Stop a program from starting with Windows.",
        "act_disable_startup_item_risk": "low: the value is saved and restored by one rollback",
        "act_dry_run": "dry-run, nothing was changed: {r}",
        "act_dup_done": "moved {n} copies to quarantine",
        "act_dup_left": "{n} copies were left in place",
        "act_dup_lost": "lost and kept copy: {p}",
        "act_dup_none": "no confirmed duplicates to quarantine",
        "act_dup_ready": "{n} redundant copies to quarantine",
        "act_env_already_ok": "{v} is already correct ({cur})",
        "act_env_dead_entry": "dead entry in {h}: {e}",
        "act_env_empty": "empty entry",
        "act_env_fixed": "{v} points to a valid folder",
        "act_env_not_in_path": "entry '{e}' is not in PATH (already cleaned?)",
        "act_env_path_unreadable": "PATH cannot be read after the change",
        "act_env_removed": "dead entry removed",
        "act_env_still_in_path": "entry {e} is still in PATH",
        "act_env_still_wrong": "{v} is still not correct ({cur})",
        "act_env_target": "{v} -> {t}",
        "act_env_unknown_var": "unknown variable: {v}",
        "act_fix_temp_var_description": "Point TEMP/TMP back to a valid temporary folder.",
        "act_fix_temp_var_risk": "low: the old value is saved, rollback restores it exactly",
        "act_precondition_failed": "precondition failed: {r}",
        "act_proxy_done": "proxy disabled",
        "act_proxy_not_on": "proxy is not enabled (ProxyEnable != 1)",
        "act_proxy_on": "proxy is enabled, disabling it",
        "act_proxy_still_on": "proxy is still enabled (ProxyEnable={e})",
        "act_quarantine_duplicates_description": "Move redundant identical copies to quarantine (one stays).",
        "act_quarantine_duplicates_risk": "medium: the first copy stays, the rest go to quarantine; rollback restores everything",
        "act_remove_path_entry_description": "Remove a dead entry from the PATH variable.",
        "act_remove_path_entry_risk": "low: the old value is saved, rollback restores it exactly",
        "act_restart_service_description": "Stop and start a service that had stopped.",
        "act_restart_service_risk": "medium: a brief service interruption; if it crashes again, verify fails and the state is restored",
        "act_snapshot_failed": "snapshot failed: {e}",
        "act_startup_disabled": "{e} is no longer in startup",
        "act_startup_exists": "entry exists: {v}",
        "act_startup_gone": "entry disappeared between precondition and snapshot",
        "act_startup_missing": "entry {e} does not exist (already disabled?)",
        "act_startup_still": "{e} is still present",
        "act_svc_exists": "service {s} exists (state: {state})",
        "act_svc_gone": "service {s} disappeared",
        "act_svc_missing": "service {s} does not exist",
        "act_svc_running": "{s} is running",
        "act_svc_start_failed": "start failed: {e}",
        "act_svc_state": "{s} state: {now}",
        "act_temp_done": "cleaned {n} files",
        "act_temp_left": "{n} files left in place",
        "act_temp_no_dir": "folder does not exist: {d}",
        "act_temp_none": "no files older than {days} days",
        "act_temp_ready": "{n} files for quarantine",
        "act_verify_failed": "verification failed, rolled back: {d}",
        "act_win_only": "Windows only",
        "vp_no_steps": "the plan must have a non-empty 'steps' list",
        "vp_no_target": "step {i}: 'target' is missing",
        "vp_not_object": "the plan must be a JSON object",
        "vp_ok": "accepted {n} steps",
        "vp_protected": "step {i}: protected zone '{p}'",
        "vp_step_not_object": "step {i} is not an object",
        "vp_too_many": "too many steps ({n} > {max})",
        "vp_unknown_action": "step {i}: action '{a}' is not in the catalog ({allowed})",
        "up_bad_version": "invalid version: {v}",
        "up_download_failed": "download failed: {e}",
        "up_no_asset": "no file to download",
        "up_sha_mismatch": "sha256 mismatch — file rejected",
        "up_unreachable": "cannot reach {u}: {e}",
        "cli_unknown_scanner": "unknown scanner '{n}'",
        "cli_update_available": "New version: {new} (have {cur}).",
        "cli_update_check_failed": "Update check failed: {e}",
        "cli_update_failed": "Update failed: {e}",
        "cli_update_uptodate": "Version {v} is the latest.",
        "act_proxy_changed": "the proxy state changed before the snapshot",
        "act_env_path_gone": "PATH disappeared between precondition and snapshot",
        "act_hosts_changed": "the hosts file changed more than planned",
        "act_hosts_done": "removed {n} entry(ies) ({ip} {host})",
        "act_hosts_gone": "entry {ip} {host} disappeared before the snapshot",
        "act_hosts_no_file": "hosts file does not exist: {p}",
        "act_hosts_not_found": "entry {ip} {host} is not in the hosts file",
        "act_hosts_ready": "entry {ip} {host} is in the hosts file",
        "act_hosts_still": "entry {ip} {host} is still in the hosts file",
        "act_hosts_unreadable": "hosts file cannot be read: {e}",
        "act_remove_hosts_entry_description": "Remove a suspicious entry from the hosts file (restore on request).",
        "act_remove_hosts_entry_risk": "medium: hosts is a DNS protection; the snapshot keeps the whole file and rollback restores it",
        "act_disable_power_saver_description": "Switch the power plan back to Balanced.",
        "act_disable_power_saver_risk": "low: only the active plan changes; the snapshot keeps the old GUID and rollback restores it",
        "act_power_already": "the power plan is already Balanced",
        "act_power_done": "the power plan is now Balanced",
        "act_power_gone": "the active plan changed before the snapshot",
        "act_power_ready": "another plan is active ({guid}), switching to Balanced",
        "act_power_still": "the power plan was not changed (active: {guid})",
        "act_power_unreadable": "the active power plan cannot be read: {e}",
        "act_remove_share_description": "Remove a network share you did not create on purpose (restore on request).",
        "act_remove_share_risk": "medium: the share is closed to the network; the snapshot keeps the path and rollback restores it",
        "act_share_default": "share {n} is a system (administrative) share — left alone",
        "act_share_done": "share {n} was removed from the network",
        "act_share_gone": "share {n} disappeared before the snapshot",
        "act_share_missing": "share {n} does not exist",
        "act_share_ready": "share {n} points to {p}",
        "act_share_still": "share {n} is still present",
        "act_share_unreadable": "the share cannot be read: {e}",
        "sc_disk_almost_full_title": "Disk is almost full ({gb} GB left)",
        "sc_disk_almost_full_why": ("When free space runs out Windows slows "
                                    "down, updates fail and programs crash "
                                    "while saving."),
        "sc_disk_almost_full_impact": "risk of program crashes and failed updates",
        "sc_disk_temp_cache_risk": ("low: we only remove temp and cache that "
                                    "rebuilds itself"),
        "sc_disk_low_title": "Little free space ({gb} GB)",
        "sc_disk_low_why": ("Under 20% free — time to clean up before it "
                            "becomes critical."),
        "sc_disk_low_impact": "slowdown and risk of a full disk",
        "sc_disk_temp_title": "Temporary files take up {gb} GB",
        "sc_disk_temp_why": ("Temp is never cleaned on its own; leftovers from "
                             "old installs and cache can grow to several "
                             "gigabytes."),
        "sc_disk_temp_impact": "about {gb} GB would be freed",
        "sc_disk_temp_risk": ("low: only files older than 7 days go to "
                              "quarantine (30 days)"),
        "sc_disk_wu_title": "Windows Update cache takes up {gb} GB",
        "sc_disk_wu_why": ("Downloaded update packages stay on disk after "
                           "installation."),
        "sc_disk_wu_impact": "about {gb} GB would be freed",
        "sc_disk_wu_risk": "low: the cache is re-downloaded if needed",
        "sc_disk_old_title": "Old Windows installation ({gb} GB)",
        "sc_disk_old_why": ("The Windows.old folder remains after an upgrade; "
                            "Windows deletes it after ~10 days, but until "
                            "then it eats disk space."),
        "sc_disk_old_impact": "about {gb} GB would be freed",
        "sc_disk_old_risk": ("medium: once deleted there is no going back to "
                             "the old version"),
        "cli_summary": ("Your computer has {n} problems.\n"
                         "  {c} critical  {m} medium  {l} low"),
        "summary_fixable": "Can be fixed automatically: {n}.",
        "summary_no_autofix": "No finding has an automatic fix — see the "
                              "recommendations in the findings.",
        "ai_settings": "AI: on/off",
        "audit_saved": "Run log saved: {p}",
        "audit_failed": "Run log not saved: {e}",
        "lang_label": "Language:",
        "lang_restart": "Language saved — it applies the next time the app starts.",
        "ai_state_now": "AI: {s}",
        "ai_state_on": "on",
        "ai_state_off": "off (offline mode)",
        "ai_example_none": ("No findings yet — an example request appears after a scan."),
    },
}


def tr(key: str, lang: str = "bs", **fmt) -> str:
    text = STRINGS.get(lang, STRINGS["bs"]).get(key, key)
    return text.format(**fmt) if fmt else text
