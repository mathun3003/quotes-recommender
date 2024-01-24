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
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_HOME='/usr/local' \
    POETRY_INSTALLER_PARALLEL=1

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

# create lock file from pyproject.toml
RUN poetry lock --no-update

# export lock file to requirements.txt
RUN poetry export -f requirements.txt --output requirements.txt

# install dependencies
RUN pip3 install -r requirements.txt

# copy project content
COPY . /app

# expose port
EXPOSE 8501

# set entrypoint
ENTRYPOINT ["streamlit", "run", "quotes_recommender/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
