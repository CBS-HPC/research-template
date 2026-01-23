"""
Registry management - JSON persistence for remote configurations.
"""

import json
import os
import pathlib
from datetime import datetime


def _atomic_write_json(path: str, data: dict):
    """Atomically write JSON to avoid corruption."""
    path = pathlib.Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)


def load_registry(remote_name: str, json_path: str = "./bin/rclone_remote.json") -> tuple[str | None, str | None]:
    """
    Load rclone remote mapping.

    Returns:
        (remote_path, local_path) or (None, None) if not found
    """
    if not os.path.exists(json_path):
        print(f"No rclone registry found at {json_path}")
        return None, None

    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print("Could not parse rclone registry file — it may be corrupted.")
        return None, None
    except OSError as e:
        print(f"Failed to read rclone registry: {e}")
        return None, None

    entry = data.get(remote_name)
    if not isinstance(entry, dict):
        return None, None

    return entry.get("remote_path"), entry.get("local_path")


def save_registry(
    remote_name: str,
    folder_path: str,
    local_backup_path: str,
    remote_type: str,
    json_path: str = "./bin/rclone_remote.json"
):
    """Save remote configuration to registry."""
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    data = {}
    if os.path.exists(json_path):
        with open(json_path) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print("Warning: JSON file was corrupted or empty, reinitializing.")

    data[remote_name] = {
        "remote_path": f"{remote_name}:{folder_path}",
        "local_path": local_backup_path,
        "remote_type": remote_type,
        "last_action": None,
        "last_operation": None,
        "timestamp": None,
        "status": "initialized",
    }
    _atomic_write_json(json_path, data)
    print(f"Saved rclone path ({folder_path}) for '{remote_name}' to {json_path}")
    print(f"Local backup source: {local_backup_path}")
    print(f"Remote type: {remote_type}")


def load_all_registry(json_path: str = "./bin/rclone_remote.json") -> dict:
    """Load entire registry."""
    if not os.path.exists(json_path):
        return {}
    try:
        with open(json_path) as f:
            return json.load(f)
    except Exception:
        return {}


def update_sync_status(
    remote_name: str,
    action: str,
    operation: str,
    success: bool = True,
    json_path: str = "./bin/rclone_remote.json"
):
    """Update last sync status for a remote."""
    if not os.path.exists(json_path):
        return
    try:
        with open(json_path, "r") as f:
            data = json.load(f)
        if remote_name in data and isinstance(data[remote_name], dict):
            data[remote_name]["last_action"] = action
            data[remote_name]["last_operation"] = operation
            data[remote_name]["timestamp"] = datetime.now().isoformat()
            data[remote_name]["status"] = "ok" if success else "potentially corrupt"
        _atomic_write_json(json_path, data)
    except Exception as e:
        print(f"Failed to update sync status: {e}")


def delete_from_registry(remote_name: str, json_path: str = "./bin/rclone_remote.json"):
    """Remove remote from registry."""
    if os.path.exists(json_path):
        try:
            with open(json_path, "r+") as f:
                data = json.load(f)
                if remote_name in data:
                    del data[remote_name]
                    f.seek(0)
                    f.truncate()
                    json.dump(data, f, indent=2)
                    print(f"Removed '{remote_name}' entry from {json_path}.")
        except Exception as e:
            print(f"Error updating JSON config: {e}")