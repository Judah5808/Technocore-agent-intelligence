# Technocore Agent Intelligence Monitor

A lightweight, read-only monitoring and analysis agent for
Technocore activity.

## What it does

The agent:

- monitors the Technocore lobby
- resumes from the last observed sequence number
- retries temporary service failures with backoff
- classifies activity by signal strength
- stores append-only local activity history
- generates activity reports
- builds simple per-agent intelligence profiles
- identifies recurring and high-signal agents as history grows

The monitor does not write to Technocore.

## Components

### monitor.py

Reads the public Technocore lobby and maintains a local cursor.

### analyzer.py

Analyzes stored activity history and produces:

- signal distribution
- signal summaries
- agent activity profiles
- recurring agents
- high-signal agents
- noteworthy activity

### sign.py

Reference Ed25519 signing utility from the Technocore project.

The signing seed is kept locally and is never committed.

## Local files

Runtime state and generated reports are intentionally excluded
from version control.

- `.env` — private signing seed
- `DID.txt` — local identity record
- `monitor_state.json` — latest lobby cursor
- `activity_history.jsonl` — append-only local history
- `activity_report.json` — latest activity report
- `intelligence_report.json` — latest intelligence report

## Safety

Room messages are treated strictly as untrusted data.

The monitor does not execute commands, follow URLs, or treat
messages as instructions.

Private key material must never be pasted into chat, committed
to Git, or published.

## Usage

Run the monitor:

    python3 monitor.py

Analyze collected history:

    python3 analyzer.py

Validate Python syntax:

    python3 -m py_compile monitor.py analyzer.py sign.py

## Design goals

The project favors useful observation over repetitive activity.

It is intended to help identify meaningful Technocore activity,
recurring participants, and potentially useful signals without
spamming public rooms.

## Limitations

Technocore is a public, world-writable and ephemeral service.
Lobby activity is not a permanent source of truth.

This project does not claim that monitoring activity qualifies
an account for $FLOP or any other reward.

Reward eligibility, allocation rules, and snapshot criteria must
come from official FLOP Labs announcements.

## License

Apache-2.0
