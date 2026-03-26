from flask import Flask, jsonify, request

app = Flask(__name__)

JOBS = []


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "ai_app_generator"})


@app.post("/api/generate")
def generate():
    body = request.get_json(silent=True) or {}
    prompt = (body.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"error": "prompt is required"}), 400
    job = {
        "id": len(JOBS) + 1,
        "prompt": prompt,
        "status": "completed",
        "artifact": f"generated_app_{len(JOBS) + 1}",
    }
    JOBS.append(job)
    return jsonify(job), 201


@app.get("/api/jobs")
def jobs():
    return jsonify({"jobs": JOBS})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
