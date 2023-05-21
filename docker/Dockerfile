FROM python:3.10-slim-bullseye as python
ENV DEBIAN_FRONTEND=noninteractive
ENV LC_ALL=C.UTF-8 LANG=C.UTF-8
# Do not write .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# Do not ever buffer console output
ENV PYTHONUNBUFFERED 1
# We need gettext to get the envsubst command
# and git is nice to have in the dev container
RUN \
    apt-get update && \
    apt-get install --no-install-recommends -y curl gettext git ffmpeg build-essential portaudio19-dev && \
    rm -r /var/cache/apt /var/lib/apt

WORKDIR /app

FROM python as poetry
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN python -c 'from urllib.request import urlopen; print(urlopen("https://install.python-poetry.org").read().decode())' | python -
COPY . /app/
RUN poetry install --no-interaction --no-ansi -vvv

FROM python as runtime
COPY --from=poetry /app /app
RUN useradd -ms /bin/bash salman
RUN chown -R salman /app

USER salman
ENV PATH="/app/.venv/bin:$PATH"
RUN python -m spacy download en_core_web_sm
CMD ["tail", "-f", "/dev/null"]
