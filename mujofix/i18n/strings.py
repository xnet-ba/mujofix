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
