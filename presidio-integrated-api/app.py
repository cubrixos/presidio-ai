from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

ANALYZER_URL = "https://presidio-analyzer-nrztwvtmga-uc.a.run.app/analyze"
ANONYMIZER_URL = "https://presidio-anonymizer-nrztwvtmga-uc.a.run.app/anonymize"

@app.route('/integrate', methods=['POST'])
def integrate():
    data = request.json
    text = data.get("text")
    entities = data.get("entities", ["PERSON", "PHONE_NUMBER"])

    if not text:
        return jsonify({"error": "Text is required"}), 400

    # Step 1: Analyze Text
    analyzer_payload = {
        "text": text,
        "analyzer_config": {
            "entities": entities
        }
    }
    analyzer_response = requests.post(ANALYZER_URL, json=analyzer_payload)
    if analyzer_response.status_code != 200:
        return jsonify({"error": "Analyzer failed", "details": analyzer_response.text}), 500
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
    if anonymizer_response.status_code != 200:
        return jsonify({"error": "Anonymizer failed", "details": anonymizer_response.text}), 500
    anonymizer_results = anonymizer_response.json()

    return jsonify(anonymizer_results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
