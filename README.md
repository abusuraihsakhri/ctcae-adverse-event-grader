# CTCAE Adverse Event Grader

### [Open the Live Application →](https://abusuraihsakhri.github.io/ctcae-adverse-event-grader/)

A small reference calculator for **two selected NCI CTCAE v5.0 laboratory adverse-event terms**, plus preserved legacy demonstration components. The browser app works locally without a backend, account, or external service.

## Supported grading

| CTCAE v5.0 term | Input | Supported grades |
| --- | --- | --- |
| Neutrophil count decreased | Absolute neutrophil count and laboratory LLN, cells/µL | 1–4 |
| Platelet count decreased | Platelet count and laboratory LLN, cells/µL | 1–4 |

Counts at or above the laboratory lower limit of normal are reported as **no grade assigned**, not CTCAE Grade 0. Grade 5 is not defined for these two terms. Laboratory LLN is required. The calculation applies NCI v5.0 boundaries with their inclusive lower limits.

**Scope and safety:** This is a reference implementation, not a comprehensive CTCAE dictionary, medical device, treatment algorithm, or validated clinical decision support system. Verify adverse-event terminology and severity against your study protocol, current applicable CTCAE version, and clinical circumstances. No dose modification or clinical triage is calculated.

Reference: [NCI CTCAE v5.0, 27 November 2017 — Investigations](https://dctd.cancer.gov/research/ctep-trials/for-sites/adverse-events/ctcae-v5-8x11.pdf). This project deliberately implements **v5.0**, although NCI has released CTCAE v6.0; consult the [NCI adverse events resources](https://dctd.cancer.gov/research/ctep-trials/for-sites/adverse-events) for other releases.

## Browser application

Open `web/index.html` in a modern desktop or mobile browser. Select a CTCAE term, enter the measured count and your laboratory's LLN, and calculate the grade. Session results can be exported as a CSV or cleared.

**Privacy:** The static browser calculator performs calculations in JavaScript. It makes no API requests, does not retain results in browser storage, and does not transmit results. Session records are kept only in the active tab's memory until reload/close. Avoid patient identifiers in research exports.

GitHub Pages publishes the self-contained `web/` application through `.github/workflows/pages.yml`.

## Python commands

Python 3.10+:

```bash
python -m pip install -e .
ctcae-grade grade --term "Neutrophil count decreased" --value 900 --lln 1800
```

The output contains `"grade": 3`, with count units recorded as `/uL`.

To grade a CSV:

```bash
ctcae-grade batch --input counts.csv --output graded.csv
```

Input columns: `term,value,lln` (see `sample_ctcae.csv`). Additional fields are preserved; output adds `ctcae_grade,ctcae_version,grade_status`. Unsupported terms, malformed rows, duplicate headers, invalid values, and nonfinite numbers are rejected rather than silently graded.

**Legacy compatibility:** `ctcae.py` (`calculate_score`, `process_csv`, `single`, and `batch`), the `ctcae` command (`audit`, `batch`, `chat`, `verify-audit`, `serve`), and `enrichment.py` remain available. Their historical arbitrary score/alert thresholds **are not CTCAE grading rules or validated clinical scores**. The chat feature returns a deterministic mock response; it does not call an external language model or verify guidelines.

## REST API

The optional FastAPI server provides authenticated access to the CTCAE calculator and legacy demonstration interfaces:

```bash
export API_KEY="replace-with-a-strong-random-key"
export AUDIT_SECRET_KEY="replace-with-a-different-strong-random-key"
python cli.py serve
```

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/ctcae/grade \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"term":"Neutrophil count decreased","value":900,"lln":1800}'
```

Other endpoints: `GET /health` (public), `GET /metrics`, `POST /api/audit`, `POST /api/chat`, `GET /api/audit/logs`. All except health require `X-API-Key`; if no `API_KEY` is configured, protected routes return HTTP 503. FastAPI provides live OpenAPI documentation at `/docs` and `/openapi.json`.

The API's identifier screening is based on **limited regular-expression patterns**, not comprehensive PHI detection or HIPAA de-identification. Never submit identifiable patient information. The HMAC-SHA256 audit log is **in-memory only**: it detects modifications to retained entries, but it is not durable storage, and its integrity does not establish clinical correctness. Use trusted networking controls and an external authentication or audit infrastructure for any production deployment. Rotate any key copied from earlier Docker Compose revisions.

## Docker

```bash
cp .env.example .env
# Replace BOTH example keys with distinct strong random values.
docker compose up --build
```

Docker Compose binds the API to localhost (`127.0.0.1:8000`). The container runs as a non-root user. No valid keys are shipped in the repository.

## Development and verification

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m compileall -q agents ctcae.py ctcae_grading.py cli.py
node --test web/app.test.cjs
docker build -t ctcae-adverse-event-grader .
```

CI tests the package, command-line entry point, graded laboratory boundaries, invalid data handling, API authentication, browser JavaScript, and Docker health/grade routes on Linux. The browser calculator needs no Pyodide or Python runtime; current browsers with standard ES2020 JavaScript and Blob URL support suffice.

## Project structure

- `ctcae_grading.py` — NCI v5.0 reference rules, CLI and CSV batch grading.
- `web/` — self-contained static interface and JavaScript regression tests.
- `agents/` — optional FastAPI plus legacy operational demonstration and in-memory audit infrastructure.
- `ctcae.py`, `cli.py`, `enrichment.py` — retained legacy interfaces.
- `tests/` — pytest regression suite.
- `.github/workflows/` — CI and Pages deployment.

## License

[MIT](LICENSE).
