#!/usr/bin/env python3

import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone

HISTORY_FILE = "activity_history.jsonl"
OUTPUT_FILE = "intelligence_report.json"


SIGNAL_NAMES = {
    r"\btestnet\b": "testnet",
    r"\bfaucet\b": "faucet",
    r"\bbug\b": "bug",
    r"\bissue\b": "issue",
    r"\bsecurity\b": "security",
    r"\bvulnerability\b": "vulnerability",
    r"\bdocumentation\b": "documentation",
    r"\binterop": "interop",
    r"\bapi\b": "api",
    r"\bdeploy": "deployment",
    r"\brelease\b": "release",
    r"\bbuild\b": "build",
    r"\bdeveloper\b": "developer",
    r"\bdev\b": "developer",
    r"\bprotocol\b": "protocol",
    r"\bregistry\b": "registry",
    r"\bnode\b": "node",
    r"\bnetwork\b": "network",
    r"\bidentity\b": "identity",
    r"\bverified\b": "verified",
    r"\bsigned\b": "signed",
}


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []

    records = []

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return records


def signal_names_from_text(text):
    text_lower = text.lower()
    found = []

    for pattern, name in SIGNAL_NAMES.items():
        if re.search(pattern, text_lower):
            found.append(name)

    return found


def build_agent_profiles(records):
    profiles = defaultdict(lambda: {
        "messages": 0,
        "high_signal": 0,
        "medium_signal": 0,
        "low_signal": 0,
        "total_score": 0,
        "signals": Counter(),
        "first_seen": None,
        "last_seen": None,
        "sequences": [],
    })

    for record in records:
        did = record.get("from", "unknown")
        profile = profiles[did]

        profile["messages"] += 1

        category = record.get("category", "low")

        if category == "high":
            profile["high_signal"] += 1
        elif category == "medium":
            profile["medium_signal"] += 1
        else:
            profile["low_signal"] += 1

        score = record.get("score", 0)
        profile["total_score"] += score

        text = record.get("text", "")
        for signal in signal_names_from_text(text):
            profile["signals"][signal] += 1

        ts = record.get("ts")

        if ts:
            if profile["first_seen"] is None:
                profile["first_seen"] = ts

            profile["last_seen"] = ts

        seq = record.get("seq")

        if isinstance(seq, int):
            profile["sequences"].append(seq)

    result = []

    for did, profile in profiles.items():

        messages = profile["messages"]
        total_score = profile["total_score"]

        if messages:
            average_score = round(
                total_score / messages,
                2
            )
        else:
            average_score = 0

        result.append({
            "did": did,
            "messages": messages,
            "high_signal": profile["high_signal"],
            "medium_signal": profile["medium_signal"],
            "low_signal": profile["low_signal"],
            "total_score": total_score,
            "average_score": average_score,
            "signals": dict(
                profile["signals"].most_common()
            ),
            "first_seen": profile["first_seen"],
            "last_seen": profile["last_seen"],
            "sequences": profile["sequences"],
        })

    result.sort(
        key=lambda x: (
            x["messages"],
            x["total_score"],
        ),
        reverse=True,
    )

    return result


def build_signal_summary(records):
    counter = Counter()

    for record in records:
        for signal in signal_names_from_text(
            record.get("text", "")
        ):
            counter[signal] += 1

    return dict(counter.most_common())


def build_activity_summary(records):
    categories = Counter()
    scores = []

    for record in records:
        categories[
            record.get("category", "low")
        ] += 1

        scores.append(
            record.get("score", 0)
        )

    return {
        "high_signal": categories["high"],
        "medium_signal": categories["medium"],
        "low_signal": categories["low"],
        "average_score": round(
            sum(scores) / len(scores),
            2
        ) if scores else 0,
    }


def build_noteworthy(records):
    noteworthy = []

    for record in records:
        score = record.get("score", 0)

        if score >= 4:
            noteworthy.append({
                "seq": record.get("seq"),
                "ts": record.get("ts"),
                "from": record.get("from"),
                "score": score,
                "text": record.get("text"),
                "signals": signal_names_from_text(
                    record.get("text", "")
                ),
            })

    noteworthy.sort(
        key=lambda x: x.get("seq") or 0
    )

    return noteworthy[-30:]


def build_report(records):

    profiles = build_agent_profiles(records)

    recurring = [
        profile
        for profile in profiles
        if profile["messages"] >= 2
    ]

    high_signal_agents = [
        profile
        for profile in recurring
        if profile["high_signal"] > 0
        or profile["average_score"] >= 2
    ]

    signal_summary = build_signal_summary(records)

    activity_summary = build_activity_summary(records)

    report = {
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "records_analyzed": len(records),

        "summary": {
            "unique_agents": len(profiles),
            "recurring_agents": len(recurring),
            "high_signal_agents": len(
                high_signal_agents
            ),
            **activity_summary,
        },

        "signal_summary": signal_summary,

        "agent_profiles": profiles,

        "recurring_agents": recurring,

        "high_signal_agents": high_signal_agents,

        "noteworthy_activity": build_noteworthy(
            records
        ),
    }

    return report


def print_report(report):

    summary = report["summary"]

    print("\n================================")
    print("     TECHNOCORE INTELLIGENCE")
    print("================================")

    print(
        f"Records analyzed : "
        f"{report['records_analyzed']}"
    )

    print(
        f"Unique agents    : "
        f"{summary['unique_agents']}"
    )

    print(
        f"Recurring agents : "
        f"{summary['recurring_agents']}"
    )

    print(
        f"High-signal agents: "
        f"{summary['high_signal_agents']}"
    )

    print(
        f"Average score    : "
        f"{summary['average_score']}"
    )

    print("\n--- ACTIVITY ---")

    print(
        f"High   : {summary['high_signal']}"
    )

    print(
        f"Medium : {summary['medium_signal']}"
    )

    print(
        f"Low    : {summary['low_signal']}"
    )

    print("\n--- SIGNAL SUMMARY ---")

    if report["signal_summary"]:

        for name, count in report[
            "signal_summary"
        ].items():

            print(
                f"{name}: {count}"
            )

    else:
        print("No recognized signals.")

    print("\n--- RECURRING AGENTS ---")

    if report["recurring_agents"]:

        for profile in report[
            "recurring_agents"
        ]:

            print(
                f"{profile['did'][:18]}..."
                f"{profile['did'][-8:]} "
                f"-> {profile['messages']} messages, "
                f"score {profile['total_score']}"
            )

    else:

        print(
            "None yet. More history is needed."
        )

    print("\n--- HIGH-SIGNAL AGENTS ---")

    if report["high_signal_agents"]:

        for profile in report[
            "high_signal_agents"
        ]:

            print(
                f"{profile['did'][:18]}..."
                f"{profile['did'][-8:]} "
                f"-> {profile['messages']} messages, "
                f"high={profile['high_signal']}, "
                f"avg={profile['average_score']}"
            )

    else:

        print(
            "None yet."
        )

    print("\n--- NOTEWORTHY ACTIVITY ---")

    if report["noteworthy_activity"]:

        for item in report[
            "noteworthy_activity"
        ]:

            signals = ", ".join(
                item["signals"]
            )

            print(
                f"[{item['seq']}] "
                f"Score {item['score']}: "
                f"{item['text']}"
            )

            if signals:
                print(
                    f"Signals: {signals}"
                )

    else:

        print(
            "No high-signal activity found."
        )

    print("\n================================")


def main():

    records = load_history()

    if not records:

        print(
            "No activity history found."
        )

        return

    report = build_report(records)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            report,
            f,
            indent=2,
            ensure_ascii=False
        )

    print_report(report)

    print(
        f"\nIntelligence report saved: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
