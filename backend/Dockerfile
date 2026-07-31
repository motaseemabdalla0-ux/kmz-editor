# KEYMAP GIS Service — Phase 1.
#
# Plain python:slim, no GDAL system package needed — see requirements.txt
# for why (no file I/O endpoints exist yet). This keeps the image small and
# the build fast/reliable; revisit when a later phase adds format I/O.
FROM python:3.12-slim

WORKDIR /app

# Build tooling is needed transiently for a couple of scientific-stack wheels
# on some platforms; removed in the same layer so it doesn't bloat the image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY tests ./tests
COPY pyproject.toml .

RUN useradd --create-home --shell /bin/bash keymap && chown -R keymap:keymap /app
USER keymap

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/v1/health', timeout=3)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
