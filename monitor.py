#!/usr/bin/env python3

import json
import os
import re
import time
import urllib.error
import urllib.request

BASE_URL = "https://technocore.chat"
ROOM = "lobby"

STATE_FILE = "monitor_state.json"
REPORT_FILE = "activity_report.json"
HISTORY_FILE = "activity_history.jsonl"

LIMIT = 20
MAX_RETRIES = 5


SIGNAL_WEIGHTS = {
    r"\btestnet\b": 4,
    r"\bfaucet\b": 4,
    r"\bbug\b": 4,
    r"\bissue\b": 4,
    r"\bsecurity\b": 4,
    r"\bvulnerability\b": 4,

    r"\bdocumentation\b": 3,
    r"\binterop": 3,
    r"\bapi\b": 3,
    r"\bdeploy": 3,
    r"\brelease\b": 3,
    r"\bbuild\b": 2,
    r"\bdeveloper\b": 2,
    r"\bdev\b": 2,
    r"\bprotocol\b": 2,
    r"\bregistry\b": 2,
    r"\bnode\b": 2,
    r"\bnetwork\b": 2,

    r"\bidentity\b": 1,
    r"\bverified\b": 1,
    r"\bsigned\b": 1,

    r"\bheartbeat\b": -2,
    r"\bcheck[- ]?in\b": -2,
    r"\bcheckin\b": -2,
    r"\blane open\b": -2,
    r"\bnetwork alive\b": -2,
}


NOISE_WORDS = {
    "real", "key", "former", "window", "total", "meet",
    "away", "manager", "such", "fund", "mother",
    "property", "artist", "college", "employee",
    "mouth", "possible", "painting", "time", "weight",
    "end", "family", "challenge", "road", "service",
    "very", "season", "sound", "house", "study",
    "nothing", "institution", "especially", "spring",
    "check", "economy", "agentic", "narrative",
}


def load_state():
    if not os.path.exists(STATE_FILE):
        return None

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)

        return state.get("since")

    except (OSError, json.JSONDecodeError):
        return None


def save_state(since):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"since": since}, f)


def fetch_lobby(since=None):
    params = f"format=json&limit={LIMIT}"

    if since is not None:
        params += f"&since={since}"

    url = f"{BASE_URL}/r/{ROOM}?{params}"

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "technocore-monitor/1.0"
                },
            )

            with urllib.request.urlopen(
                request,
                timeout=15
            ) as response:

                raw = response.read().decode("utf-8")
                return json.loads(raw)

        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
        ) as exc:

            last_error = exc

            if attempt < MAX_RETRIES:

                wait = attempt * 3

                print(
                    f"Request failed "
                    f"(attempt {attempt}/{MAX_RETRIES}): "
                    f"{exc}. Retrying in {wait}s..."
                )

                time.sleep(wait)

    raise RuntimeError(
        "Unable to reach Technocore after "
        f"{MAX_RETRIES} attempts: {last_error}"
    )


def classify_message(text):
    text_lower = text.lower().strip()

    score = 0
    signals = []

    for pattern, weight in SIGNAL_WEIGHTS.items():

        if re.search(pattern, text_lower):

            score += weight

            signals.append(
                {
                    "pattern": pattern,
                    "weight": weight,
                }
            )

    words = re.findall(r"[a-z]+", text_lower)

    noise_count = sum(
        1
        for word in words
        if word in NOISE_WORDS
    )

    if len(words) >= 4 and noise_count >= 2:
        score -= 3

    if score >= 4:
        category = "high"

    elif score >= 2:
        category = "medium"

    else:
        category = "low"

    return category, score, signals


def append_history(messages):

    if not messages:
        return

    with open(
        HISTORY_FILE,
        "a",
        encoding="utf-8"
    ) as f:

        for message in messages:

            category, score, signals = classify_message(
                message.get("text", "")
            )

            record = {
                "observed_at": time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ",
                    time.gmtime()
                ),
                "room": ROOM,
                "seq": message.get("seq"),
                "ts": message.get("ts"),
                "from": message.get("from"),
                "text": message.get("text"),
                "category": category,
                "score": score,
                "signals": signals,
            }

            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                )
                + "\n"
            )


def create_report(messages):

    categories = {
        "high": [],
        "medium": [],
        "low": [],
    }

    for message in messages:

        category, score, signals = classify_message(
            message.get("text", "")
        )

        entry = {
            "seq": message.get("seq"),
            "ts": message.get("ts"),
            "from": message.get("from"),
            "text": message.get("text"),
            "score": score,
            "signals": signals,
        }

        categories[category].append(entry)

    report = {
        "generated_at": time.strftime(
            "%Y-%m-%dT%H:%M:%SZ",
            time.gmtime()
        ),

        "room": ROOM,

        "messages_scanned": len(messages),

        "summary": {
            "high_signal": len(categories["high"]),
            "medium_signal": len(categories["medium"]),
            "low_signal": len(categories["low"]),
        },

        "activity": categories,
    }

    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            report,
            f,
            indent=2,
            ensure_ascii=False
        )

    return report


def main():

    since = load_state()

    if since is not None:

        print(
            f"Resuming from cursor: {since}"
        )

    else:

        print(
            "No saved cursor; reading "
            "the latest lobby messages."
        )

    try:

        data = fetch_lobby(since)

    except RuntimeError as exc:

        print(f"\n{exc}")
        return

    messages = data.get(
        "messages",
        []
    )

    print(
        f"\nRoom: {data.get('room')}"
    )

    print(
        f"Messages received: {len(messages)}"
    )

    if not messages:

        print("\nNo new messages.")
        print("Cursor was not changed.")

        return

    report = create_report(messages)

    append_history(messages)

    print("\n=== ACTIVITY REPORT ===")

    print(
        f"Messages scanned : "
        f"{report['messages_scanned']}"
    )

    print(
        f"High signal      : "
        f"{report['summary']['high_signal']}"
    )

    print(
        f"Medium signal    : "
        f"{report['summary']['medium_signal']}"
    )

    print(
        f"Low signal       : "
        f"{report['summary']['low_signal']}"
    )

    for level, title in [
        ("high", "HIGH SIGNAL"),
        ("medium", "MEDIUM SIGNAL"),
    ]:

        items = report["activity"][level]

        if not items:
            continue

        print(f"\n--- {title} ---")

        for item in items:

            print(
                f"[{item['seq']}] "
                f"Score: {item['score']}"
            )

            print(
                f"Text: {item['text']}"
            )

            if item["signals"]:

                signals = ", ".join(
                    f"{x['pattern']} "
                    f"({x['weight']:+d})"
                    for x in item["signals"]
                )

                print(
                    f"Signals: {signals}"
                )

            print()

    valid_sequences = [
        message["seq"]
        for message in messages
        if isinstance(
            message.get("seq"),
            int
        )
    ]

    if valid_sequences:

        highest_seq = max(valid_sequences)

        save_state(highest_seq)

        print(
            f"Saved cursor: {highest_seq}"
        )

    print(
        f"Detailed report: {REPORT_FILE}"
    )

    print(
        f"History file: {HISTORY_FILE}"
    )


if __name__ == "__main__":
    main()
