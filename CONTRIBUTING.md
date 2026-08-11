# Contributing

## Local setup

Use Python 3.11 and Node.js 24.19.0. The supported development launcher from the repository root is:

```bash
python3 launcher.py
```

For a deterministic frontend install, use the committed lock file:

```bash
cd frontend
npm ci
```

Backend runtime dependencies and development quality tools are installed separately:

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
```

`requirements.txt` installs the complete runtime, including the local OCR and Whisper stacks.
For backend checks that do not execute local AI inference, install `requirements-base.txt` with
`requirements-dev.txt`; this is the lean dependency set used by CI.

Copy `backend/.env.example` to `backend/.env` and `frontend/.env.example` to `frontend/.env` only
when local overrides are needed. Never commit the resulting `.env` files.

## Required checks

Run backend checks from the repository root:

```bash
python -m ruff check launcher.py backend/config backend/api
python -m ruff format --check launcher.py backend/config backend/api
python -m mypy
python -m pip check
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test api config --noinput
```

Run frontend checks from `frontend/`:

```bash
npm run check
```

Use `python -m ruff format launcher.py backend/config backend/api` and `npm run format` only when intentionally
applying formatting changes. Keep mechanical formatting separate from behavioral changes.

## Change discipline

- Add or update tests for changed behavior and authorization boundaries.
- Keep migrations committed with their corresponding model changes.
- Do not weaken security settings, certificate verification, test assertions, or quality gates to
  make a check pass.
- Preserve API compatibility unless the change is explicitly documented and coordinated.
- Keep generated files, local databases, media, model weights, build output, and Office lock files
  out of commits.
