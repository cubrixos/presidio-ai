FROM python:3.9-slim

# Define build arguments and environment variables
ARG NAME
ARG NLP_CONF_FILE=presidio_analyzer/conf/default.yaml
ARG ANALYZER_CONF_FILE=presidio_analyzer/conf/default_analyzer.yaml
ARG RECOGNIZER_REGISTRY_CONF_FILE=presidio_analyzer/conf/default_recognizers.yaml
ENV PIP_NO_CACHE_DIR=1
ENV ANALYZER_CONF_FILE=${ANALYZER_CONF_FILE}
ENV RECOGNIZER_REGISTRY_CONF_FILE=${RECOGNIZER_REGISTRY_CONF_FILE}
ENV NLP_CONF_FILE=${NLP_CONF_FILE}
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"

# Set working directory
WORKDIR /usr/bin/${NAME}

# Install essential build tools and Poetry
RUN apt-get update && apt-get install -y build-essential curl \
  && curl -sSL https://install.python-poetry.org | python3 - -- --path $POETRY_HOME \
  && apt-get clean

# Copy configuration files
COPY ${ANALYZER_CONF_FILE} ./
COPY ${RECOGNIZER_REGISTRY_CONF_FILE} ./
COPY ${NLP_CONF_FILE} ./

# Copy project files
COPY pyproject.toml poetry.lock* ./

# Install project dependencies including Flask
RUN poetry install --no-root -E server

# Verify Flask installation
RUN poetry run python -c "import flask; print('Flask is installed')"

# Copy the rest of the application files
COPY . .

# Install NLP models specified in NLP_CONF_FILE
COPY install_nlp_models.py ./
RUN poetry run python install_nlp_models.py --conf_file ${NLP_CONF_FILE}

# Expose the port that the app runs on
EXPOSE 8080

# Command to run the application
CMD ["poetry", "run", "python", "app.py", "--host", "0.0.0.0"]
