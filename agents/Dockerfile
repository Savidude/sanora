FROM --platform=linux/arm64 python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv \
    && rm -rf .venv

COPY . .

# Recreate the environment inside the target Linux/ARM64 image. This prevents
# a host-created virtual environment from being used at runtime.
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONUNBUFFERED="1"

CMD ["python", "story_designer_agent.py"]
