from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import os
import openai
import logging
from io import StringIO
import time

app = Flask(__name__)

# Set up basic logging to a string buffer
log_stream = StringIO()
logging.basicConfig(level=logging.INFO, stream=log_stream, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variables
ANALYZER_URL = os.getenv("ANALYZER_URL", "https://presidio-analyzer-nrztwvtmga-uc.a.run.app/analyze")
ANONYMIZER_URL = os.getenv("ANONYMIZER_URL", "https://presidio-anonymizer-nrztwvtmga-uc.a.run.app/anonymize")
INTEGRATE_URL = os.getenv("INTEGRATE_URL", "https://presidio-integrated-api-nrztwvtmga-wl.a.run.app/integrate")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

# Default entities for the analyzer
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
    result = {"submitted_log": log}

    if not log:
        logging.info("No log submitted. Redirecting to index.")
        return redirect(url_for('index'))

    try:
        logging.info(f"Received log: {log}")

        # Track time for integrate request
        start_time = time.time()
        response = requests.post(INTEGRATE_URL, json={"text": log}, timeout=30)
        response.raise_for_status()
        end_time = time.time()

        result.update(response.json())
        logging.info(f"Received result from integrate endpoint: {result}")
        logging.info(f"Time taken for integrate request: {end_time - start_time} seconds")

    except requests.exceptions.Timeout:
        logging.error(f"Request to {INTEGRATE_URL} timed out.")
        result["error"] = "Request to integrate endpoint timed out."
    except requests.exceptions.RequestException as e:
        logging.error(f"Request to integrate endpoint failed: {e}")
        result["error"] = "Failed to process the log."
        result["details"] = str(e)

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

        # Analyzer request and timing
        start_time = time.time()
        logging.info(f"Sending text to analyzer: {analyzer_payload}")
        analyzer_response = requests.post(ANALYZER_URL, json=analyzer_payload, timeout=30)
        analyzer_response.raise_for_status()
        analyzer_results = analyzer_response.json()
        end_time = time.time()
        logging.info(f"Analyzer results: {analyzer_results}")
        logging.info(f"Time taken for analyzer request: {end_time - start_time} seconds")

        # Anonymizer request and timing
        start_time = time.time()
        logging.info(f"Sending results to anonymizer: {anonymizer_payload}")
        anonymizer_response = requests.post(ANONYMIZER_URL, json=anonymizer_payload, timeout=30)
        anonymizer_response.raise_for_status()
        anonymizer_results = anonymizer_response.json()
        end_time = time.time()
        logging.info(f"Anonymizer results: {anonymizer_results}")
        logging.info(f"Time taken for anonymizer request: {end_time - start_time} seconds")

        # GPT-4 request and timing
        start_time = time.time()
        try:
            gpt4_request = anonymizer_results['text']
            logging.info("Sending anonymized text to GPT-4 for analysis.")
            chat_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes anonymized log data."},
                    {"role": "user", "content": gpt4_request}
                ],
                max_tokens=150
            )
            gpt4_analysis = chat_response['choices'][0]['message']['content'].strip()
            logging.info(f"GPT-4 analysis result: {gpt4_analysis}")
        except Exception as e:
            logging.error(f"GPT-4 analysis failed: {e}")
            return jsonify({"error": "GPT-4 analysis failed", "details": str(e)}), 500
        end_time = time.time()
        logging.info(f"Time taken for GPT-4 request: {end_time - start_time} seconds")

        return jsonify({
            "submitted_log": text,
            "analyzer_request": analyzer_payload,
            "analyzer_results": analyzer_results,
            "anonymizer_request": anonymizer_payload,
            "anonymized_text": anonymizer_results['text'],
            "gpt4_request": gpt4_request,
            "gpt4_analysis": gpt4_analysis,
            "gpt4_recommendations": gpt4_analysis
        })

    except requests.exceptions.Timeout:
        logging.error(f"Request to one of the services timed out.")
        return jsonify({"error": "Request to one of the services timed out.", "logs": log_stream.getvalue()}), 504
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return jsonify({"error": "Request failed", "details": str(e), "logs": log_stream.getvalue()}), 500
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred", "details": str(e), "logs": log_stream.getvalue()}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
