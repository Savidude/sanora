FROM --platform=linux/arm64 python:3.12-slim

WORKDIR /app/agents

COPY agents/pyproject.toml agents/uv.lock ./
COPY packages/sanora-contracts /app/packages/sanora-contracts
COPY agents/ .
RUN pip install --no-cache-dir uv \
    && rm -rf .venv

# Recreate the environment inside the target Linux/ARM64 image. This prevents
# a host-created virtual environment from being used at runtime.
RUN uv sync --frozen --no-dev

ENV PATH="/app/agents/.venv/bin:${PATH}"
ENV PYTHONUNBUFFERED="1"

CMD ["python", "story_designer_agent.py"]
