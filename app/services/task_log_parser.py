"""Parse task_log text field into structured entries and checklist items.

Expected format in task_log:
    ## 2026-04-24 14:30
    Some log content here.

    ## Action Items
    - [x] Completed task
    - [ ] Pending task

    ## 2026-04-23 09:00
    Earlier log entry.
"""
import re


def parse_task_log(text):
    """Parse task_log text into structured data.

    Returns dict with:
        entries: list of {"timestamp": str, "content": str} (newest first)
        checklist: list of {"text": str, "done": bool}
    """
    if not text or not text.strip():
        return {"entries": [], "checklist": []}

    entries = []
    checklist = []

    lines = text.split("\n")
    current_entry = None

    for line in lines:
        ts_match = re.match(r"^##\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})", line)
        if ts_match:
            if current_entry:
                entries.append(current_entry)
            current_entry = {"timestamp": ts_match.group(1), "content": ""}
            continue

        # Skip ## Action Items section header to avoid duplication on rebuild
        if re.match(r"^##\s*Action\s+Items", line, re.IGNORECASE):
            continue

        check_match = re.match(r"^-\s*\[([ xX])\]\s*(.+)$", line)
        if check_match:
            checklist.append({
                "text": check_match.group(2).strip(),
                "done": check_match.group(1).lower() == "x",
            })
            continue

        if current_entry is not None:
            current_entry["content"] += line + "\n"

    if current_entry:
        entries.append(current_entry)

    for entry in entries:
        entry["content"] = entry["content"].strip()

    return {"entries": entries, "checklist": checklist}


def rebuild_task_log(entries, checklist):
    """Rebuild task_log text from structured data.

    Args:
        entries: list of {"timestamp": str, "content": str} (newest first, will be reversed)
        checklist: list of {"text": str, "done": bool}

    Returns:
        str: formatted task_log text
    """
    parts = []

    for entry in entries:
        parts.append(f"## {entry['timestamp']}")
        if entry["content"]:
            parts.append(entry["content"])
        parts.append("")

    if checklist:
        parts.append("## Action Items")
        for item in checklist:
            mark = "x" if item["done"] else " "
            parts.append(f"- [{mark}] {item['text']}")
        parts.append("")

    return "\n".join(parts).strip()


def add_log_entry(text, content):
    """Add a new timestamped log entry to task_log text.

    Returns updated task_log text.
    """
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    parsed = parse_task_log(text)
    parsed["entries"].insert(0, {"timestamp": timestamp, "content": content})

    return rebuild_task_log(parsed["entries"], parsed["checklist"])


def toggle_checklist_item(text, item_text):
    """Toggle a checklist item's done status.

    Returns updated task_log text.
    """
    parsed = parse_task_log(text)
    for item in parsed["checklist"]:
        if item["text"] == item_text:
            item["done"] = not item["done"]
            break
    return rebuild_task_log(parsed["entries"], parsed["checklist"])
