# CTCAE Adverse Event Grader

> **Domain:** Diagnostic Radiology & Medical Imaging AI
> **Reference Guidelines & Standards:** American College of Radiology (ACR) RADS & Fleischner Society

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## What It Does

CTCAE v5 grading for common adverse events from lab/vital thresholds. Points-based scoring with tiered action thresholds. Includes a multi-agent supervisor system with HMAC-SHA256 tamper-evident audit trail and zero-PHI outbound guard.

---

## Installation

### Option 1: pip
```bash
pip install -r requirements.txt
```

### Option 2: Docker
```bash
docker build -t ctcae-adverse-event-grader .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key ctcae-adverse-event-grader
```

### Option 3: Docker Compose
```bash
docker-compose up -d
```

---

## Usage

### CLI Commands

#### Single Evaluation
```bash
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2
```

#### Batch CSV Processing
```bash
python cli.py batch -i input.csv -o results.csv
```

#### Chat Query
```bash
python cli.py chat "Explain the grading criteria"
```

#### Verify Audit Trail
```bash
python cli.py verify-audit
```

#### Start API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Core Scoring Module
```python
import ctcae

# Calculate score from patient factors
result = ctcae.calculate_score({'age': 68, 'sex': 'M', 'cancer': 1})
print(result)  # {'score': 3, 'tier': 'moderate', 'detail': {...}}

# Process CSV file
results = ctcae.process_csv('input.csv', 'output.csv')
```

### API Endpoints

| Endpoint | Method | Description |
|:---------|:-------|:------------|
| `/health` | GET | Health check |
| `/metrics` | GET | Prometheus-style metrics |
| `/api/audit` | POST | Submit task for evaluation |
| `/api/chat` | POST | Query the supervisor |
| `/api/audit/logs` | GET | Get audit trail |

---

## Configuration

| Environment Variable | Description | Default |
|:---------------------|:------------|:--------|
| `AUDIT_SECRET_KEY` | HMAC key for audit trail integrity | Random (ephemeral) |
| `MODEL_PROVIDER` | LLM provider (`mock`, `ollama`, `claude`, `openai`) | `mock` |

> **Security Note:** Always set `AUDIT_SECRET_KEY` in production. Without it, a random key is generated on startup and audit integrity cannot be verified across restarts.

---

## Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest -v --cov=agents --cov=ctcae

# Run simulation benchmark
python simulator.py 1000
```

---

## Architecture

- **`ctcae.py`** — Core scoring engine with points-based algorithm
- **`cli.py`** — Command-line interface
- **`agents/`** — Multi-agent supervisor system:
  - `supervisor.py` — Orchestrates worker evaluations
  - `workers.py` — Specialized domain workers (QC, Safety, Protocol)
  - `base.py` — PHI guard, HMAC audit trail, security utilities
  - `models.py` — Pydantic data models
  - `api.py` — FastAPI REST endpoints
  - `llm_factory.py` — LLM provider abstraction
  - `metrics.py` — Prometheus metrics exporter
  - `learning.py` — Bayesian calibration engine
  - `streamer.py` — WebSocket telemetry broadcaster
- **`enrichment.py`** — Extended feature engines
- **`simulator.py`** — High-throughput stress testing

---

## Security Features

- **Zero-PHI Outbound Guard:** AST and regex inspection blocking SSNs, MRNs, phone numbers, emails, and patient identifiers
- **HMAC-SHA256 Tamper-Evident Audit Trail:** Chained, cryptographically signed logs with integrity verification
- **Input Validation:** All inputs validated before processing
- **Error Handling:** Graceful error handling with informative messages

---

## License

MIT License - see [LICENSE](LICENSE) for details.
