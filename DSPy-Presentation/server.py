from pathlib import Path
import json
from flask import Flask, jsonify, send_from_directory
from run_pipelines import load_email, get_pipeline_results

ROOT = Path(__file__).resolve().parent
app = Flask(__name__, static_folder=str(ROOT), static_url_path='')

EMAIL_PATH = ROOT / 'data' / 'email.json'

@app.route('/')
def index():
    return send_from_directory(str(ROOT), 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(str(ROOT), path)

@app.route('/api/email')
def api_email():
    email_text = load_email(EMAIL_PATH)
    return jsonify({'email': email_text})

@app.route('/api/results')
def api_results():
    email_text = load_email(EMAIL_PATH)
    results = get_pipeline_results(email_text)
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=False)
