#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Tiran
#
# Created:     09/12/2025
# Copyright:   (c) Tiran 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------
from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# === הגדרות Adafruit IO שלך ===
AIO_USERNAME = "braude1"   # השם שלך ב-Adafruit IO
AIO_KEY = os.environ.get("AIO_KEY")  # נכניס כ-Environment ב-Render

BASE_URL = f"https://io.adafruit.com/api/v2/{AIO_USERNAME}"

VALID_FEEDS = {"humidity", "json", "soil", "temperature"}


@app.route("/history", methods=["GET"])
def history():
    feed_key = request.args.get("feed")
    limit_str = request.args.get("limit", "20")

    if not AIO_KEY:
        return jsonify({"error": "AIO_KEY is not configured on server"}), 500

    if not feed_key:
        return jsonify({"error": "missing 'feed' query parameter"}), 400

    if feed_key not in VALID_FEEDS:
        return jsonify({
            "error": "invalid feed",
            "allowed_feeds": sorted(list(VALID_FEEDS))
        }), 400

    try:
        limit = int(limit_str)
    except ValueError:
        limit = 20

    if limit <= 0:
        limit = 1
    if limit > 200:
        limit = 200

    url = f"{BASE_URL}/feeds/{feed_key}/data"
    headers = {"X-AIO-Key": AIO_KEY}
    params = {"limit": limit}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=5)
    except Exception as e:
        return jsonify({"error": f"request to Adafruit IO failed: {e}"}), 502

    if resp.status_code != 200:
        return jsonify({
            "error": "Adafruit IO returned an error",
            "status_code": resp.status_code,
            "details": resp.text
        }), 502

    try:
        data = resp.json()
    except Exception as e:
        return jsonify({"error": f"failed to parse JSON from Adafruit: {e}"}), 500

    cleaned = [
        {
            "value": d.get("value"),
            "created_at": d.get("created_at")
        }
        for d in data
    ]

    return jsonify({
        "feed": feed_key,
        "count": len(cleaned),
        "data": cleaned
    })


@app.route("/latest", methods=["GET"])
def latest():
    feed_key = request.args.get("feed")

    if not AIO_KEY:
        return jsonify({"error": "AIO_KEY is not configured on server"}), 500

    if not feed_key:
        return jsonify({"error": "missing 'feed' query parameter"}), 400

    if feed_key not in VALID_FEEDS:
        return jsonify({
            "error": "invalid feed",
            "allowed_feeds": sorted(list(VALID_FEEDS))
        }), 400

    url = f"{BASE_URL}/feeds/{feed_key}/data"
    headers = {"X-AIO-Key": AIO_KEY}
    params = {"limit": 1}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=5)
    except Exception as e:
        return jsonify({"error": f"request to Adafruit IO failed: {e}"}), 502

    if resp.status_code != 200:
        return jsonify({
            "error": "Adafruit IO returned an error",
            "status_code": resp.status_code,
            "details": resp.text
        }), 502

    data = resp.json()
    if not data:
        return jsonify({"error": "no data in feed"}), 404

    latest_sample = data[0]

    return jsonify({
        "feed": feed_key,
        "value": latest_sample.get("value"),
        "created_at": latest_sample.get("created_at")
    })
