from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import os
import openai

app = Flask(__name__)

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
        return redirect(url_for('index'))

    # Call the integrate endpoint with the submitted log
    response = requests.post(INTEGRATE_URL, json={"text": log})
    result = response.json()

    return render_template('index.html', result=result)

@app.route('/integrate', methods=['POST'])
def integrate():
    try:
        data = request.json
        text = data.get("text")
        entities = data.get("entities", DEFAULT_ENTITIES)
        language = data.get("language", "en")

        if not text:
            return jsonify({"error": "Text is required"}), 400

        # Step 1: Analyze Text
        analyzer_payload = {
            "text": text,
            "language": language,
            "analyzer_config": {
                "entities": entities
            }
        }
        analyzer_response = requests.post(ANALYZER_URL, json=analyzer_payload)
        analyzer_response.raise_for_status()
        analyzer_results = analyzer_response.json()

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
        anonymizer_response = requests.post(ANONYMIZER_URL, json=anonymizer_payload)
        anonymizer_response.raise_for_status()
        anonymizer_results = anonymizer_response.json()

        # Step 3: Send the Anonymized Log to OpenAI Codex for Analysis
        try:
            codex_response = openai.Completion.create(
                engine="davinci-codex",
                prompt=anonymizer_results['text'],
                max_tokens=150
            )
            codex_analysis = codex_response.choices[0].text.strip()
        except Exception as e:
            return jsonify({"error": "Codex analysis failed", "details": str(e)}), 500

        # Combine and return the results
        return jsonify({
            "analyzer_results": analyzer_results,
            "anonymized_text": anonymizer_results['text'],
            "codex_analysis": codex_analysis
        })

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Request failed", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

