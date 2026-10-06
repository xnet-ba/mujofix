# Contributing (MujoFix)

## Proces
- `main` je zaštićen — rad kroz feature grane + PR (min. 1 review).
- Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `build:`).
- Mali koraci: max ~5 fajlova po PR-u bez dogovora.
- Svaki PR: testovi prolaze (`python -m unittest discover -s tests`),
  `py_compile` čist, bez TODO-a u kritičnom kodu.

## Pravila koda (iz AGENTS.md)
- Samo stdlib gdje god može; nove zavisnosti uz obrazloženje.
- Svaka akcija koja mijenja sistem: rizik + `rollback()` + test
  apply → verify → rollback → identično stanje.
- `netestirano` oznaka za sve što nije prošlo VM listu (docs/TESTING.md).
- Zabranjeno: `--dangerously-skip-permissions`, `--auto` u bilo kojoj komandi;
  OpenCode proces nikad elevated; MCP alati nikad ne mijenjaju sistem.
- Sintetički test podaci; nikad pravi logovi, ključevi ni skenirani podaci.

## Sigurnost
- Tajne (tokene, ključeve) nikad u kod/logove. Pre-commit: gitleaks.
- Ranjivost? Ne otvaraj javni Issue — vidi SECURITY.md.
