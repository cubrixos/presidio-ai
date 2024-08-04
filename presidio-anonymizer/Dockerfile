FROM python:3.9-slim

# Define build arguments and environment variables
ARG NAME
ENV PIP_NO_CACHE_DIR=1

# Set working directory
WORKDIR /usr/bin/${NAME}

# Install essential build tools and Poetry
RUN apt-get update && apt-get install -y build-essential curl \
  && curl -sSL https://install.python-poetry.org | python3 - \
  && apt-get clean

# Copy project files
COPY pyproject.toml poetry.lock* ./

# Install project dependencies including Flask
RUN poetry install --no-root -E server

# Copy the rest of the application files
COPY . .

# Expose the port that the app runs on
EXPOSE 8080

# Command to run the application
CMD ["poetry", "run", "python", "app.py", "--host", "0.0.0.0"]
