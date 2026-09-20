# Local development image; Compose supplies the source bind mount.
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install -r requirements.txt

RUN groupadd --gid 1000 django \
    && useradd --uid 1000 --gid django --create-home django \
    && chown django:django /app

COPY --chown=django:django . .

USER django

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
