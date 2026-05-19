# Releases — `pip`

## [0.1.0] — initial

- `/pip` skill body — wraps `pip` (or `python -m pip`) and reports a
  concise verdict.
- Provider overrides : Claude Code (`Bash(pip *)`, `Bash(python -m pip *)`),
  GitHub Copilot (`runCommands` + `terminalLastCommand`), OpenCode
  (defaults).
- No hooks (skill-only bundle).
