import json

def extract_json_logs(caplog):
    """
    Extract JSON-formatted log lines from caplog.text.
    This works because our log handler writes JSON to stderr,
    which pytest captures in caplog.text.
    """

    json_logs = []

    # caplog.text contains the raw JSON output exactly as shown
    for line in caplog.text.splitlines():
        line = line.strip()

        # only look at lines that start with '{'
        if not line.startswith("{"):
            continue

        try:
            parsed = json.loads(line)
            json_logs.append(parsed)
        except Exception:
            continue

    return json_logs
