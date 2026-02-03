FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m app && chown -R app:app /app
USER app

RUN git clone https://github.com/Jak0ub/CLI_Chatter . \
    && rm -rf .git

RUN python3 -m venv venv
ENV PATH="/app/venv/bin:$PATH"

RUN pip install --no-cache-dir -r req.txt

CMD ["python3", "server.py"]
