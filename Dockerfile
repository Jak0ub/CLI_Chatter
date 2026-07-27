FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN apt-get update

RUN useradd -m app && chown -R app:app /app
USER app

#Venv outside of WORKDIR so it can't be overwritten
RUN python3 -m venv /home/app/venv

ENV PATH="/home/app/venv/bin:$PATH"
#For a beter build times
COPY --chown=app:app req.txt .
RUN pip install --no-cache-dir -r req.txt

COPY --chown=app:app . .

CMD ["python3", "server.py"]
