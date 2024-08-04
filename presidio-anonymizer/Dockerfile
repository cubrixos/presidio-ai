FROM python:3.9-slim

# Define build arguments and environment variables
ARG NAME
ENV PIP_NO_CACHE_DIR=1

# Set the working directory
WORKDIR /usr/bin/${NAME}

# Copy the current directory contents into the container
COPY . .

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Increase pip's default timeout
RUN pip config set global.timeout 1000

# Install the necessary libraries
RUN pip install --no-cache-dir -r requirements.txt

# Verify Flask installation
RUN python -c "import flask; print('Flask is installed')"

# Log installed packages
RUN pip list

# Verify packages in runtime environment
CMD ["sh", "-c", "pip list && python -c 'import flask; print(\"Flask is installed\")' && python app.py --host 0.0.0.0"]

# Expose the port that the app runs on
EXPOSE 8080
