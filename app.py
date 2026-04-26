from flask import Flask, render_template, request, jsonify
import requests, json, os
from pathlib import Path

app = Flask(__name__)

NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "l7n8F9keGoEPOZn94frN")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "fVHlSmF3N2")
QUEUE_FILE = Path("queue.json")


def load_queue():
    if QUEUE_FILE.exists():
        return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
    return []


def save_queue(q):
    QUEUE_FILE.write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    start = max(1, int(request.args.get("start", 1)))
    if not q:
        return jsonify([])
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {"query": q, "display": 9, "start": start, "sort": "sim", "filter": "all"}
    try:
        r = requests.get("https://openapi.naver.com/v1/search/image",
                         headers=headers, params=params, timeout=10)
        r.raise_for_status()
        items = r.json().get("items", [])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify(items)


@app.route("/queue", methods=["GET"])
def get_queue():
    return jsonify(load_queue())


@app.route("/queue", methods=["POST"])
def add_queue():
    item = request.get_json()
    if not item or not item.get("url") or not item.get("filename"):
        return jsonify({"error": "url, filename 필요"}), 400
    q = load_queue()
    # 같은 파일명 중복 방지
    q = [x for x in q if x.get("filename") != item["filename"]]
    q.append(item)
    save_queue(q)
    return jsonify({"ok": True, "count": len(q)})


@app.route("/queue/clear", methods=["POST"])
def clear_queue():
    save_queue([])
    return jsonify({"ok": True})


@app.route("/queue/remove", methods=["POST"])
def remove_queue():
    filename = (request.get_json() or {}).get("filename")
    if filename:
        q = [x for x in load_queue() if x.get("filename") != filename]
        save_queue(q)
    return jsonify({"ok": True, "count": len(load_queue())})


if __name__ == "__main__":
    app.run(debug=True)
