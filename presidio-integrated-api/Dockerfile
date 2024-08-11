FROM python:3.9-slim

# Set environment variables
ENV ANALYZER_URL=https://presidio-analyzer-nrztwvtmga-uc.a.run.app/analyze
ENV ANONYMIZER_URL=https://presidio-anonymizer-nrztwvtmga-uc.a.run.app/anonymize
ENV INTEGRATE_URL=https://presidio-integrated-api-nrztwvtmga-wl.a.run.app/integrate
ENV OPENAI_API_KEY=OPENAI_API_KEY


# Set the working directory
WORKDIR /usr/src/app

# Copy the current directory contents into the container
COPY . .

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Install the necessary libraries
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that the app runs on
EXPOSE 8080

# Command to run the application
CMD ["python", "app.py", "--host", "0.0.0.0"]
