# Salman
the terminal-based personal AI assistant

## Introduction
Salman is a terminal-based personal AI assistant written in python. It's not intended for production use, but rather as a fun project that I intend to run in a raspberry pi inside a [fish](https://en.wikipedia.org/wiki/Big_Mouth_Billy_Bass).

Features:
- Runs as a terminal app.
- Can be controlled by voice commands through [whisper](https://github.com/openai/whisper)
- Can store "facts" it learns about you in a local graph database using [neo4j](https://neo4j.com)
- Searches the internet for things it does not know.
- Uses as few calls for LLM inference as I could make it do to reduce LLM costs.

Weird choices:
- Salman uses a graph db to store its knowledge. That's because I liked the idea of being able to visualize the knowledge graph. It would be a lot easier and more effective to use a vector db for semantic searches.
- I use Anthropic AI's Claude as an LLM. That's mostly because I don't like OpenAI as a company. If you use OpenAI, please feel free to submit a PR. It should be about changing a few lines. When there is a good open source alternative, I will switch to it.

## Installation

You can use Docker with the provided `docker-compose.yml`. You will need first to provide some configuration:

- Edit the file in `docker/config/salman.env` to set your name by changing the `HUMAN` env variable. 
- You will need to provide your Anthropic API key in the `ANTHROPIC_API_KEY` env variable. This should be set in `docker/secrets/keys.env`

Build everything with `docker-compose build`. Then, run `docker-compose up -d` to start the container.

You can now run salman with `docker exec -it salman salman`.

## Development

It's very akward to develop a terminal app inside docker. What I find most convenient is to run the container with `docker-compose up -d` and then run salman on the host. To do so, create a `.env` file in the root of the project with the same keys as above. Then, run in a virtual env.

```
python3.10 -m venv venv
source venv/bin/activate
pip install poetry 
poetry install
salman
```

If you want to see logs and debug, you can use `textual's` console. In a separate terminal I usually do:
```
textual console -x EVENT
```
and then run salman through textual.
```
textual run --dev -c salman
```

## Contributing
I am more than happy to accept contributions. Please PR away.
