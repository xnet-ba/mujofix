# Security policy (MujoFix)

## Prijava ranjivosti
Ne otvaraj javni Issue za sigurnosne probleme. Piši na
https://github.com/xnet-ba/mujofix/security/advisories/new
(navedi verziju, Windows build, korake reprodukcije, uticaj).
Odgovaramo u roku od 7 dana; koordinirana objava fix-a prije detalja.

## Šta je u scope-u
- Zaobilaženje validatora/akcijske allowliste (npr. AI predloži brisanje izvan kataloga, a prođe).
- Rollback koji ne vrati stanje; karantin koji trajno briše.
- MCP (stdio) koji se spawn-uje bez izolovanog config-home, ili config koji
  se stapa sa korisničkim globalnim (tuđi MCP serveri/pluginovi u našem agentu).
- Curenje privatnih podataka u AI payload-u ili logovima.

## Šta NIJE ranjivost
- SmartScreen upozorenje (build nije potpisan — poznato, dokumentovano).
- Zen modeli kažu nešto netačno (očekivano; validator i evidence su odbrana).

## Tvrde garancije kojih se držimo
- Nijedan MCP alat ne mijenja sistem (samo čitanje + validacija).
- Bez odobrenja korisnika se NIŠTA ne mijenja.
- Nema lokalnog servera: nikad `opencode serve`, nikad port ni lozinka, ništa se
  ne izlaže na mreži (živi model je `opencode run` kao child proces).
- OpenCode proces nikad elevated; nikad `--dangerously-skip-permissions`.
