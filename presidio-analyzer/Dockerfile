# Use an official Python runtime as a parent image
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

# Set the working directory
WORKDIR /usr/bin/${NAME}

# Copy the configuration files
COPY ${ANALYZER_CONF_FILE} ./
COPY ${RECOGNIZER_REGISTRY_CONF_FILE} ./
COPY ${NLP_CONF_FILE} ./

# Copy the current directory contents into the container at /app
COPY . .

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Increase pip's default timeout
RUN pip config set global.timeout 1000

# Install the necessary libraries
RUN pip install --no-cache-dir -r requirements.txt

# Verify Flask installation
RUN python -c "import flask; print('Flask is installed')"

# Expose the port that the app runs on
EXPOSE 8080

# Command to run the application
CMD ["python", "app.py", "--host", "0.0.0.0"]
