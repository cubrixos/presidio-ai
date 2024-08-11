from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import os
import openai
import logging
from io import StringIO

app = Flask(__name__)

# Set up basic logging to a string buffer
log_stream = StringIO()
logging.basicConfig(level=logging.INFO, stream=log_stream)

# Read the service URLs from environment variables
ANALYZER_URL = os.getenv("ANALYZER_URL", "https://presidio-analyzer-nrztwvtmga-uc.a.run.app/analyze")
ANONYMIZER_URL = os.getenv("ANONYMIZER_URL", "https://presidio-anonymizer-nrztwvtmga-uc.a.run.app/anonymize")
INTEGRATE_URL = os.getenv("INTEGRATE_URL", "https://presidio-integrated-api-nrztwvtmga-wl.a.run.app/integrate")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

DEFAULT_ENTITIES = [
    "PERSON",
    "PHONE_NUMBER",
    "EMAIL_ADDRESS",
    "CREDIT_CARD",
    "IP_ADDRESS",
    "DATE_TIME",
    "NRP",
    "LOCATION",
    "BANK_ACCOUNT",
    "IBAN_CODE",
    "US_PASSPORT",
    "UK_NHS",
    "US_DRIVER_LICENSE",
    "US_ITIN",
    "US_SSN",
    "UUID"
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit-log', methods=['POST'])
def submit_log():
    log = request.form.get('log')
    if not log:
        logging.info("No log submitted. Redirecting to index.")
        return redirect(url_for('index'))

    try:
        # Log the received log data
        logging.info(f"Received log: {log}")

        # Call the integrate endpoint with the submitted log
        response = requests.post(INTEGRATE_URL, json={"text": log}, timeout=15)
        response.raise_for_status()
        result = response.json()

        # Log the result from the integrate endpoint
        logging.info(f"Received result from integrate endpoint: {result}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Request to integrate endpoint failed: {e}")
        result = {
            "error": "Failed to process the log.",
            "details": str(e),
            "logs": log_stream.getvalue()
        }

    # Add the logs to the result before rendering the template
    result['logs'] = log_stream.getvalue()

    return render_template('index.html', result=result)

@app.route('/integrate', methods=['POST'])
def integrate():
    try:
        data = request.json
        text = data.get("text")
        entities = data.get("entities", DEFAULT_ENTITIES)
        language = data.get("language", "en")

        if not text:
            logging.warning("No text provided in the request.")
            return jsonify({"error": "Text is required"}), 400

        # Step 1: Analyze Text
        analyzer_payload = {
            "text": text,
            "language": language,
            "analyzer_config": {
                "entities": entities
            }
        }
        logging.info(f"Sending text to analyzer: {analyzer_payload}")
        analyzer_response = requests.post(ANALYZER_URL, json=analyzer_payload, timeout=10)
        analyzer_response.raise_for_status()
        analyzer_results = analyzer_response.json()
        logging.info(f"Analyzer results: {analyzer_results}")

        # Step 2: Anonymize the Analyzed Text
        anonymizer_payload = {
            "text": text,
            "anonymizer_config": {
                "operators": {
                    "DEFAULT": {
                        "type": "replace",
                        "new_value": "<REDACTED>"
                    }
                }
            },
            "analyzer_results": analyzer_results
        }
        logging.info(f"Sending results to anonymizer: {anonymizer_payload}")
        anonymizer_response = requests.post(ANONYMIZER_URL, json=anonymizer_payload, timeout=10)
        anonymizer_response.raise_for_status()
        anonymizer_results = anonymizer_response.json()
        logging.info(f"Anonymizer results: {anonymizer_results}")

        # Step 3: Send the Anonymized Log to GPT-4 for Analysis
        try:
            logging.info("Sending anonymized text to GPT-4 for analysis.")
            chat_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes anonymized log data."},
                    {"role": "user", "content": anonymizer_results['text']}
                ],
                max_tokens=150
            )
            gpt4_analysis = chat_response['choices'][0]['message']['content'].strip()
            logging.info(f"GPT-4 analysis result: {gpt4_analysis}")
        except Exception as e:
            logging.error(f"GPT-4 analysis failed: {e}")
            return jsonify({"error": "GPT-4 analysis failed", "details": str(e)}), 500

        # Combine and return the results
        return jsonify({
            "analyzer_results": analyzer_results,
            "anonymized_text": anonymizer_results['text'],
            "gpt4_analysis": gpt4_analysis,
            "logs": log_stream.getvalue()
        })

    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return jsonify({"error": "Request failed", "details": str(e), "logs": log_stream.getvalue()}), 500
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred", "details": str(e), "logs": log_stream.getvalue()}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
