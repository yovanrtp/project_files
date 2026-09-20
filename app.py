from flask import Flask, jsonify
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)

# Automatically exposes /metrics
metrics = PrometheusMetrics(app)


@app.get("/")
def home():
    return jsonify(
        application="jenkins-eks-demo",
        status="ok",
        version="1.0.0"
    )


@app.get("/health")
def health():
    return jsonify(status="healthy"), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)