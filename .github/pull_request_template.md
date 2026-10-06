## Šta i zašto
<!-- Link na Issue + jedna rečenica -->

## Checklist
- [ ] Testovi prolaze (`python -m unittest discover -s tests`)
- [ ] Bez TODO-a u kritičnom kodu; max ~5 fajlova
- [ ] Nova akcija: ima `rollback()` + test apply→verify→rollback→identično
- [ ] Novi nalaz: ima `evidence`; ne tvrdi uzrok bez dokaza
- [ ] Ako dira Windows API: upisano u docs/TESTING.md kao stavka (ili već pokriveno)
- [ ] Bez tajni, tokena i pravih korisničkih logova u diff-u
