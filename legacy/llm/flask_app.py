
from flask import Flask, jsonify, send_file, render_template
import json

app = Flask(__name__, template_folder='templates')

with open("/workspace/llm_project/api/detections.json", encoding="utf-8") as f:
    detections = json.load(f)

with open("/workspace/llm_project/api/explanations.json", encoding="utf-8") as f:
    explanations = json.load(f)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/video")
def video():
    return send_file("/workspace/llm_project/demo.mp4", mimetype="video/mp4")

@app.route("/detections")
def get_detections():
    return jsonify(detections)

@app.route("/explanations")
def get_explanations():
    return jsonify(explanations)

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
