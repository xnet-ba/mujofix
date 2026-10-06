<div align="center">

# 🛠️ MujoFix

### AI mechanic for your Windows PC

**Click SCAN — the app finds issues, explains them in plain language, proposes a fix plan, you approve, it fixes, verifies, and rolls back if anything goes wrong.**

[![Status](https://img.shields.io/badge/status-Phase_6-blue)](docs/STATUS.md)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/Windows-10%20%7C%2011-blue)](docs/STATUS.md)

[Bosanski/Hrvatski/Srpski verzija](README.md)

</div>

---

## ❓ What is MujoFix

MujoFix is an **open-source desktop app** that helps a non-technical user keep a Windows PC healthy. Instead of cryptic errors, the user sees:

> **"Your PC has 7 issues. 🔴 2 critical &nbsp; 🟠 3 medium &nbsp; 🟢 2 low"**

…and one **[ FIX ALL ]** button, with an expandable list (*"Show technical details"*) for advanced users.

- Windows 10 (22H2) and Windows 11 (23H2+), x64. Works **without admin rights** (profile-level fixes); UAC elevation only when needed, explained beforehand.
- **Nothing changes without approval** (all / per-item / nothing).
- Every fix: snapshot → execute → **verify** → automatic **rollback** on failure.
- Fully usable **offline, without AI** (offline mode is the default until consent).

## 🔄 How it works

1. **SCAN** — parallel scanner plugins, progress bar, cancellable.
2. **ANALYZE** — each finding: severity (`CRITICAL / MEDIUM / LOW`), impact, fix risk, reversibility flag.
3. **PLAN** — AI drafts steps, order, time/risk estimates. User approves.
4. **EXECUTE → VERIFY → ROLLBACK** — per-step snapshots; failed verification restores the step automatically.
5. **REPORT** — before/after (freed GB, boot time, startup items) + **"Undo all"**.

Anti-hallucination: the AI talks **only about evidence the scanner collected**; uncertainty is explicit; every proposal passes a validator (JSON schema + action allowlist). The AI never executes anything — a deterministic executor runs only catalog actions.

## 🧩 Scanners

Startup, services, disk, network, configuration, drivers, large files & duplicates (never auto-deleted, review only), suspicious processes ("suspicious, reasons: …" — never "virus"), permissions (disabled UAC = CRITICAL, ACLs, shares). Every module degrades gracefully on unsupported Windows versions.

## 🤖 AI layer

Bundled, pinned OpenCode as a child process (`opencode serve`, 127.0.0.1 only, per-launch password). The `mujofix` agent has **all built-in tools denied** — only MujoFix MCP tools (read-only + plan validator). Fallback chain: model A → B → C → offline. Consent screen first (what is sent, to whom, real payload example); anonymized before sending; Zen free-tier data terms: **unconfirmed**.

## 🛡️ Safety

Hard-coded blacklist (System32, WinSxS, boot config, BitLocker, Defender read-only…), System Restore Point where allowed, file quarantine (30 days, not deletion), registry exports, dry-run mode, full audit log. Never disables antivirus/firewall/updates.

## 🚦 Status

Phases 0–6 implemented as code with 100 passing mocked unit tests. **Nothing has been validated on a real Windows machine yet** — see [docs/TESTING.md](docs/TESTING.md) (manual Win10/Win11 VM checklist). No signed build, no public release until the VM list passes.

## ⚠️ Disclaimer

**This tool changes system settings and comes WITHOUT ANY WARRANTY.** Back up important data first. Changes can only be undone within the built-in rollback (30-day quarantine, restore point). Nothing here is "100% safe".
