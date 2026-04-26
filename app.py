from flask import Flask, render_template, request, jsonify
import requests, json, os
from pathlib import Path

app = Flask(__name__)

NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "l7n8F9keGoEPOZn94frN")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "fVHlSmF3N2")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
GOOGLE_CX = os.environ.get("GOOGLE_CX", "")
QUEUE_FILE = Path("queue.json")
EPISODES_FILE = Path("episodes.json")


def load_queue():
    if QUEUE_FILE.exists():
        return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
    return []


def save_queue(q):
    QUEUE_FILE.write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/episodes")
def episodes():
    if EPISODES_FILE.exists():
        return jsonify(json.loads(EPISODES_FILE.read_text(encoding="utf-8")))
    return jsonify([])


@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    engine = request.args.get("engine", "naver")
    start = max(1, int(request.args.get("start", 1)))
    if not q:
        return jsonify([])

    if engine == "google":
        if not GOOGLE_API_KEY or not GOOGLE_CX:
            return jsonify({"error": "Google API 키 미설정"}), 400
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CX,
            "q": q,
            "searchType": "image",
            "num": 9,
            "start": start,
        }
        try:
            r = requests.get("https://www.googleapis.com/customsearch/v1",
                             params=params, timeout=10)
            r.raise_for_status()
            raw = r.json().get("items", [])
            items = [{"link": i["link"], "thumbnail": i["image"]["thumbnailLink"],
                      "title": i["title"]} for i in raw]
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        return jsonify(items)

    # naver (default)
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {"query": q, "display": 9, "start": start, "sort": "sim"}
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
