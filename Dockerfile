FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY pyproject.toml README.md LICENSE ./
COPY agents/ ./agents/
COPY cli.py ctcae.py ctcae_grading.py enrichment.py simulator.py ./

RUN pip install --no-cache-dir . && \
    useradd --system --no-create-home --uid 10001 ctcae

USER ctcae

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1

CMD ["python", "cli.py", "serve", "--host", "0.0.0.0", "--port", "8000"]
