# Bundle — `pip`

Skill-only bundle that ships the `/pip` slash command. Runs any pip
operation (`install`, `freeze`, `list`, `show`, `uninstall`, ...) off
the parent context to keep multi-thousand-line resolver / install
output out of the assistant's window.

## Installation

```
/smith-bundle-install --name pip --ia claude-code
/smith-bundle-install --name pip --ia github-copilot
/smith-bundle-install --name pip --ia opencode
```

Requires `/smith-init` on the consumer project.

## Usage

```
/pip install -r requirements.txt
/pip install --upgrade requests
/pip freeze
/pip list --outdated
/pip uninstall some-pkg
```

The assistant returns a concise verdict (`OK` / `FAIL`) + counters and
the failure cause when relevant — never the full resolver log.

## Tags

`build`, `python`, `python3`.
