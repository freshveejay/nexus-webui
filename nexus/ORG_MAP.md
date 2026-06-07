# NEXUS Org-Map

An entry point inside NEXUS (Open WebUI) that surfaces ORKY's live **org
ontology** — the map of personas, groups, and knowledge-base access.

- ORKY service: `http://192.168.1.115:9470`
- Org-Map endpoint: `http://192.168.1.115:9470/org-map`

This is **additive and read-only**. It does not call the model, mutate chats,
or touch the database. It only surfaces a link/iframe to the ORKY service on the
LAN.

There are two install options. Option A (Function) is the primary, in-product
path. Option B (link/iframe panel) is a documented fallback if you prefer not to
register a Function.

---

## Option A — Install the Org-Map Function (recommended)

File: [`nexus/functions/org_map.py`](functions/org_map.py)

It is an OpenWebUI **Action** function (`class Action`), matching the same
filter/function pattern used by `nexus/functions/nate_b_jones_rag.py`. When a
user clicks the **Org-Map** toolbar button, it emits a chat message with a
clickable link plus an inline iframe of `/org-map`.

### Install via the Admin UI

1. Sign in to NEXUS as an admin (the live shell is `http://192.168.1.124:3080`).
2. Go to **Admin Panel → Functions → +** (New Function / Import).
3. Paste the contents of `nexus/functions/org_map.py`, or import the file.
4. Save. Give it the id `org_map` if prompted.
5. Toggle the function **on** (Enabled).
6. (Optional) Open the function's **Valves** and confirm:
   - `org_map_url` = `http://192.168.1.115:9470/org-map`
   - `embed_iframe` = `true` (set `false` for a link-only card)
   - `iframe_height` = `720`

### Install by copying the file into the container

The repo mounts `nexus/` into the image. If functions are auto-loaded from
disk in your deployment, copy the file and let Open WebUI pick it up:

```bash
docker cp nexus/functions/org_map.py aimsho-webui:/app/nexus/functions/org_map.py
# then register/enable it once via Admin Panel → Functions (import from path or paste)
```

### Use

Open any chat, click the **Org-Map** action button in the message toolbar. A
card with the link and an embedded `/org-map` iframe is posted into the chat.

### Valves reference

| Valve | Default | Purpose |
|-------|---------|---------|
| `enabled` | `true` | Master on/off switch |
| `org_map_url` | `http://192.168.1.115:9470/org-map` | ORKY org-map endpoint |
| `iframe_height` | `720` | Height (px) of the embedded iframe |
| `embed_iframe` | `true` | Inline iframe vs link-only card |

---

## Option B — Link / iframe panel (no Function)

If you would rather not register a Function, expose the Org-Map as a static
link or iframe.

### B1. Sidebar / nav link

In **Admin Panel → Settings → Interface**, add a custom/external link if your
build exposes one, pointing at:

```
http://192.168.1.115:9470/org-map
```

### B2. Standalone iframe page

Drop a small HTML file next to the other static assets and open it directly:

```html
<!-- static/org-map.html -->
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>NEXUS Org-Map</title>
    <style>html,body,iframe{margin:0;height:100%;width:100%;border:0}</style>
  </head>
  <body>
    <iframe src="http://192.168.1.115:9470/org-map" title="NEXUS Org-Map"></iframe>
  </body>
</html>
```

Reachable at `http://192.168.1.124:3080/static/org-map.html` (path depends on
how static assets are served in your build).

---

## Notes

- The iframe loads ORKY over plain HTTP on the LAN. If NEXUS is later served
  over HTTPS, browsers may block the mixed-content iframe — in that case use the
  link-only mode (`embed_iframe=false`) or serve ORKY over HTTPS.
- ORKY must be reachable from the user's browser (Option B iframe) or from the
  NEXUS container/browser context. Confirm with:
  `curl -sS -o /dev/null -w '%{http_code}\n' http://192.168.1.115:9470/org-map`
