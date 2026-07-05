# Commit Guidelines

This repo follows [Conventional Commits](https://www.conventionalcommits.org/).
Every commit message must have this shape:

```
<type>(<scope>): <short summary>

<optional body>
```

## Type

| Type       | Use for |
|------------|---------|
| `feat`     | New capability (endpoint, page, script, service) |
| `fix`      | Bug fix |
| `chore`    | Tooling, config, dependencies, ignore rules — no behavior change for end users |
| `docs`     | README, CLAUDE.md, `docs/`, comments-only changes |
| `refactor` | Restructuring code with no behavior change |
| `style`    | Formatting only (whitespace, naming) — no logic change |
| `test`     | Adding or fixing tests |

## Scope

Scope names the area touched, matching the repo layout in `CLAUDE.md`:

- `backend-core` — `backend/config.py`, `db.py`, `models.py`, `scheduler.py`, `app.py`
- `routers` — `backend/routers/`
- `services` — `backend/services/`
- `frontend` — `frontend/`
- `src` — the standalone CLI scripts in `src/`
- `tooling` — dev scripts, `.devcontainer/`, startup scripts
- `config` — `.gitignore`, `.env.example`, `requirements.txt`, root config
- `docs` — `README.md`, `CLAUDE.md`, `docs/`

Omit the scope only when a change is genuinely repo-wide.

## Summary line

- Imperative mood: "add", not "added"/"adds".
- No period at the end.
- ~72 characters max.

## Body (optional)

Explain *why*, not what — the diff already shows what changed. Use it for
context that isn't obvious from the code (a constraint, a workaround, a
decision). Skip it for self-explanatory changes.

## Author

Commits in this repo are authored solely by the repo owner. Do not add
`Co-Authored-By` trailers or any AI-attribution footer, regardless of what
tool assisted in drafting the change.

## Splitting changes

Prefer one commit per logical area (see Scope above) over one giant commit.
A commit should leave the repo in a coherent state — don't split a single
feature's backend and its router registration across commits if one doesn't
work without the other.

## Examples

```
feat(routers): add /portfolio endpoints for positions and performance

feat(frontend): add Watchlist page with mirrored politician trades

fix(src): load FMP/FRED credentials from .env in politician_tracker

chore(config): ignore frontend build artifacts and local sqlite db

docs: document backend setup and .env variables in SETUP.md
```
