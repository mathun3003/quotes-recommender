FROM python:3.11.6

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    # Python
    PYTHONUNBUFFERED=1 \
    # pip
    PIP_NO_CACHE_DIR=1 \
    # poetry:
    POETRY_VERSION=1.7.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_HOME='/usr/local' \
    POETRY_INSTALLER_PARALLEL=true

# upgrade deps
RUN apt-get update && apt-get upgrade -y

# Install poetry for package management
RUN python -m pip install "poetry==$POETRY_VERSION" \
    && export PATH="/root/.local/bin:$PATH" \
    && poetry --version

# Use /app as the working directory
WORKDIR /app

# copy pyproject.toml file
COPY pyproject.toml /app

# install dependencies
RUN poetry install --sync --no-ansi --no-root -vvv

# change shell profile
SHELL ["/bin/bash", "-c"]

# activate venv
RUN source $(poetry env info --path)/bin/activate

# copy project content
COPY . /app

# expose port
EXPOSE 8501

# set entrypoint
ENTRYPOINT ["poetry", "run", "streamlit", "run", "quotes_recommender/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
