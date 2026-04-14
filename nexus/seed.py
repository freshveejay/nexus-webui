"""
NEXUS Seed Script for Open WebUI
Pre-configures the database with NEXUS personas, user groups, and connections.
Run after first startup: python -m nexus.seed
"""

import json
import os
import sqlite3
import time
import uuid
from pathlib import Path

# Default DB path matches Open WebUI's default
DB_PATH = os.getenv("NEXUS_DB_PATH", "/app/backend/data/webui.db")
ADMIN_USER_ID = None  # Will be detected from existing admin


# ─── NEXUS Personalities as Model Configs ────────────────────────────────────

NEXUS_MODELS = [
    {
        "id": "nexus-base",
        "name": "NEXUS Base",
        "base_model_id": "nvidia/nemotron-3-super-120b-a12b",
        "params": {
            "system": (
                "You are NEXUS, an AI assistant deployed at a 65-person Hollywood trailer house. "
                "You run locally on DGX Spark hardware with 640GB unified memory. You help with "
                "post-production workflows across DaVinci Resolve, Premiere Pro, After Effects, "
                "Cinema 4D, and other industry tools. Be professional, precise, and deeply aware "
                "of film/TV post-production terminology and workflows. Reference specific tools, "
                "techniques, and industry standards when relevant."
            ),
            "temperature": 0.7,
            "max_tokens": 4096,
        },
        "meta": {
            "profile_image_url": "/static/nexus/nexus-base.png",
            "description": "General-purpose post-production assistant. Knows all the tools.",
            "tags": [{"name": "General"}, {"name": "Post-Production"}],
            "capabilities": {"vision": True, "usage": True},
        },
    },
    {
        "id": "nexus-counsel",
        "name": "Counsel",
        "base_model_id": "nvidia/nemotron-3-super-120b-a12b",
        "params": {
            "system": (
                "You are Counsel, NEXUS's legal and compliance persona at a Hollywood trailer house. "
                "You assist with contract review, licensing terms, delivery specifications, and "
                "regulatory compliance for broadcast and streaming distribution. You know Netflix IMF "
                "specs, Apple ProRes requirements, Amazon delivery guidelines, and broadcast standards "
                "inside out. Always cite relevant standards and specifications. Emphasize risk awareness "
                "without being alarmist. When unsure, recommend consulting the legal department."
            ),
            "temperature": 0.3,
            "max_tokens": 4096,
        },
        "meta": {
            "profile_image_url": "/static/nexus/counsel.png",
            "description": "Legal & compliance. Delivery specs, licensing, contracts.",
            "tags": [{"name": "Legal"}, {"name": "Compliance"}],
        },
    },
    {
        "id": "nexus-muse",
        "name": "Muse",
        "base_model_id": "nvidia/nemotron-3-super-120b-a12b",
        "params": {
            "system": (
                "You are Muse, NEXUS's creative ideation persona at a Hollywood trailer house. "
                "You help with trailer concepts, visual storytelling, color palette suggestions, "
                "sound design ideas, editorial pacing, and creative problem-solving. Think in terms "
                "of emotional beats, audience psychology, genre conventions, and cinematic language. "
                "Reference successful trailers, films, and creative techniques. Be inspired but "
                "practical - every idea should be executable with the tools at hand (Resolve, "
                "Premiere, AE, C4D)."
            ),
            "temperature": 0.9,
            "max_tokens": 4096,
        },
        "meta": {
            "profile_image_url": "/static/nexus/muse.png",
            "description": "Creative ideation. Trailer concepts, visual storytelling, sound design.",
            "tags": [{"name": "Creative"}, {"name": "Ideation"}],
            "capabilities": {"vision": True},
        },
    },
    {
        "id": "nexus-quant",
        "name": "Quant",
        "base_model_id": "nvidia/nemotron-3-super-120b-a12b",
        "params": {
            "system": (
                "You are Quant, NEXUS's data analysis persona at a Hollywood trailer house. "
                "You help analyze production metrics, render times, asset utilization, project "
                "timelines, storage capacity, and resource allocation. Be quantitative, precise, "
                "and data-driven. Present findings in structured formats with clear metrics. Help "
                "identify bottlenecks, optimize workflows, and forecast resource needs. Reference "
                "specific production metrics and industry benchmarks."
            ),
            "temperature": 0.4,
            "max_tokens": 4096,
        },
        "meta": {
            "profile_image_url": "/static/nexus/quant.png",
            "description": "Data analysis. Production metrics, render times, resource planning.",
            "tags": [{"name": "Analytics"}, {"name": "Data"}],
        },
    },
    {
        "id": "nexus-dispatch",
        "name": "Dispatch",
        "base_model_id": "nvidia/nemotron-3-super-120b-a12b",
        "params": {
            "system": (
                "You are Dispatch, NEXUS's operations and scheduling persona at a Hollywood trailer "
                "house. You help coordinate team tasks, delivery schedules, render queues, asset "
                "handoffs, client review sessions, and cross-department workflows. Be efficient, "
                "action-oriented, and aware of dependencies between editorial, graphics, color, "
                "audio, and delivery. Track deadlines, flag conflicts, and suggest optimal task ordering."
            ),
            "temperature": 0.5,
            "max_tokens": 4096,
        },
        "meta": {
            "profile_image_url": "/static/nexus/dispatch.png",
            "description": "Operations & scheduling. Task coordination, delivery tracking.",
            "tags": [{"name": "Operations"}, {"name": "Scheduling"}],
        },
    },
]


# ─── NEXUS User Groups ──────────────────────────────────────────────────────

NEXUS_GROUPS = [
    {
        "name": "Creative",
        "description": "Image generation, music, TTS, creative chat. Access to Muse and NEXUS Base.",
        "permissions": {
            "workspace": {"models": True, "knowledge": False, "prompts": True},
            "chat": {"temporary": True, "file_upload": True, "edit": True, "delete": True},
        },
    },
    {
        "name": "Analyst",
        "description": "RAG, document search, data analysis, VLM. Access to Quant and NEXUS Base.",
        "permissions": {
            "workspace": {"models": True, "knowledge": True, "prompts": True},
            "chat": {"temporary": True, "file_upload": True, "edit": True, "delete": True},
        },
    },
    {
        "name": "Operator",
        "description": "Voice, TTS, dispatch, chat. Access to Dispatch and NEXUS Base.",
        "permissions": {
            "workspace": {"models": True, "knowledge": False, "prompts": True},
            "chat": {"temporary": True, "file_upload": True, "edit": True, "delete": True},
        },
    },
    {
        "name": "Manager",
        "description": "Dashboard, reports, RAG. Access to Quant, Dispatch, and NEXUS Base.",
        "permissions": {
            "workspace": {"models": True, "knowledge": True, "prompts": True},
            "chat": {"temporary": True, "file_upload": True, "edit": True, "delete": True},
        },
    },
]

# Which models each group can access
GROUP_MODEL_ACCESS = {
    "Creative": ["nexus-base", "nexus-muse"],
    "Analyst": ["nexus-base", "nexus-quant"],
    "Operator": ["nexus-base", "nexus-dispatch"],
    "Manager": ["nexus-base", "nexus-quant", "nexus-dispatch"],
}


# ─── Seed Functions ──────────────────────────────────────────────────────────

def get_admin_user_id(db: sqlite3.Connection) -> str:
    """Find the first admin user ID."""
    cursor = db.execute("SELECT id FROM user WHERE role = 'admin' LIMIT 1")
    row = cursor.fetchone()
    if row:
        return row[0]
    # No admin yet - return a placeholder
    return "nexus-seed-admin"


def seed_models(db: sqlite3.Connection, admin_id: str):
    """Insert NEXUS model configs if they don't exist."""
    now = int(time.time())
    for model in NEXUS_MODELS:
        cursor = db.execute("SELECT id FROM model WHERE id = ?", (model["id"],))
        if cursor.fetchone():
            print(f"  Model '{model['name']}' already exists, skipping")
            continue

        db.execute(
            "INSERT INTO model (id, user_id, base_model_id, name, params, meta, is_active, updated_at, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                model["id"],
                admin_id,
                model["base_model_id"],
                model["name"],
                json.dumps(model["params"]),
                json.dumps(model["meta"]),
                True,
                now,
                now,
            ),
        )
        print(f"  Created model: {model['name']} (base: {model['base_model_id']})")
    db.commit()


def seed_groups(db: sqlite3.Connection, admin_id: str):
    """Insert NEXUS user groups if they don't exist."""
    now = int(time.time())
    group_ids = {}

    for group in NEXUS_GROUPS:
        cursor = db.execute("SELECT id FROM 'group' WHERE name = ?", (group["name"],))
        row = cursor.fetchone()
        if row:
            group_ids[group["name"]] = row[0]
            print(f"  Group '{group['name']}' already exists, skipping")
            continue

        group_id = str(uuid.uuid4())
        group_ids[group["name"]] = group_id

        db.execute(
            "INSERT INTO 'group' (id, user_id, name, description, data, meta, permissions, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                group_id,
                admin_id,
                group["name"],
                group["description"],
                json.dumps({}),
                json.dumps({}),
                json.dumps(group["permissions"]),
                now,
                now,
            ),
        )
        print(f"  Created group: {group['name']}")
    db.commit()

    # Set model access per group via access_grant table
    for group_name, model_ids in GROUP_MODEL_ACCESS.items():
        group_id = group_ids.get(group_name)
        if not group_id:
            continue
        for model_id in model_ids:
            cursor = db.execute(
                "SELECT id FROM access_grant WHERE resource_type = 'model' AND resource_id = ? "
                "AND principal_type = 'group' AND principal_id = ?",
                (model_id, group_id),
            )
            if cursor.fetchone():
                continue
            grant_id = str(uuid.uuid4())
            db.execute(
                "INSERT INTO access_grant (id, resource_type, resource_id, principal_type, principal_id, permission, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (grant_id, "model", model_id, "group", group_id, "read", now),
            )
            print(f"    Granted '{group_name}' access to model '{model_id}'")
    db.commit()


def seed_config(db: sqlite3.Connection):
    """Set default NEXUS configuration in the config table."""
    # Check if config table exists and has data
    try:
        cursor = db.execute("SELECT data FROM config LIMIT 1")
        row = cursor.fetchone()
        if row:
            config = json.loads(row[0]) if row[0] else {}
        else:
            config = {}
    except Exception:
        config = {}

    # Set NEXUS defaults
    updates = {
        "ui": {
            **(config.get("ui", {})),
            "default_models": "nexus-base",
            "WEBUI_NAME": "NEXUS",
        },
    }

    # Merge with existing config
    config.update(updates)

    from datetime import datetime
    now_dt = datetime.utcnow().isoformat()
    if db.execute("SELECT COUNT(*) FROM config").fetchone()[0] > 0:
        db.execute("UPDATE config SET data = ?, updated_at = ? WHERE rowid = 1", (json.dumps(config), now_dt))
    else:
        db.execute(
            "INSERT INTO config (data, version, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (json.dumps(config), 0, now_dt, now_dt),
        )
    db.commit()
    print("  Default model set to nexus-base")
    print("  UI name set to NEXUS")


def main():
    print("\n" + "=" * 60)
    print("NEXUS Seed Script for Open WebUI")
    print("=" * 60)

    # Find the database
    db_path = DB_PATH
    if not os.path.exists(db_path):
        # Try local dev path
        local_paths = [
            "./backend/data/webui.db",
            "../data/webui.db",
            "./data/webui.db",
        ]
        for p in local_paths:
            if os.path.exists(p):
                db_path = p
                break
        else:
            print(f"  ERROR: Database not found at {DB_PATH}")
            print("  Set NEXUS_DB_PATH or run Open WebUI first to create the database.")
            return

    print(f"\n  Database: {db_path}")

    db = sqlite3.connect(db_path)

    # Check tables exist
    tables = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    if "model" not in tables:
        print("  ERROR: 'model' table not found. Run Open WebUI first to initialize the database.")
        db.close()
        return

    admin_id = get_admin_user_id(db)
    print(f"  Admin user: {admin_id}\n")

    print("[1/3] Seeding model configs...")
    seed_models(db, admin_id)

    print("\n[2/3] Seeding user groups...")
    seed_groups(db, admin_id)

    print("\n[3/3] Setting default configuration...")
    seed_config(db)

    db.close()

    print("\n" + "=" * 60)
    print("  NEXUS seed complete!")
    print("  Restart Open WebUI to apply changes.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
