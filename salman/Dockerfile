FROM python:3.9-slim-bullseye

ENV DEBIAN_FRONTEND=noninteractive
ENV LC_ALL=C.UTF-8 LANG=C.UTF-8

# Do not write .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# Do not ever buffer console output
ENV PYTHONUNBUFFERED 1

RUN \
    apt-get update && \
    apt-get install --no-install-recommends -y curl gettext git ffmpeg build-essential && \
    rm -r /var/cache/apt /var/lib/apt

COPY poetry.lock pyproject.toml README.md /app/
COPY salman /app/salman

RUN useradd -ms /bin/bash salman
RUN chown -R salman /app
WORKDIR /app
USER salman
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

RUN pip install poetry

RUN poetry build
RUN pip install ./dist/salman-0.1.0-py3-none-any.whl

CMD ["workers"]
