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
        "ai_settings": "AI: uključi/isključi",
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
        "ai_settings": "AI: on/off",
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
