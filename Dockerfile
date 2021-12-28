FROM python:3.10-alpine as base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

FROM python:3.10-slim as builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt update
RUN apt install build-essential gcc -y
RUN pip install poetry wheel
RUN python -m venv /venv

COPY pyproject.toml poetry.lock ./

RUN poetry export -f requirements.txt --without-hashes | /venv/bin/pip install -r /dev/stdin

COPY sophie_bot sophie_bot
RUN poetry build && /venv/bin/pip install dist/*.whl

FROM base as final

# RUN apk add --no-cache libffi libpq

COPY --from=builder /venv /venv

WORKDIR /app

CMD ["sh", "-c", "source /venv/bin/activate; python -m sophie_bot"]