"""
title: Org-Map
author: baseshot
version: 1.0.0
description: Adds an Org-Map entry point to NEXUS that links to ORKY's live org ontology map (/org-map). Renders a clickable card + embeddable iframe pointing at the ORKY service.
required_open_webui_version: 0.5.0
category: action
"""

from typing import Optional
from pydantic import BaseModel, Field


class Action:
    """
    OpenWebUI Action function.

    Adds an "Org-Map" button to the message toolbar. When invoked it emits a
    chat message containing a link and an embedded iframe that loads ORKY's
    /org-map view (the org ontology: personas, groups, KB access).

    This is ADDITIVE and read-only: it does not call the model, mutate any
    chat, or touch the database. It only surfaces a link/iframe to the ORKY
    service running on the LAN.
    """

    class Valves(BaseModel):
        enabled: bool = Field(
            default=True, description="Enable/disable the Org-Map action button"
        )
        org_map_url: str = Field(
            default="http://192.168.1.115:9470/org-map",
            description="ORKY org-map endpoint",
        )
        iframe_height: int = Field(
            default=720, description="Height (px) of the embedded org-map iframe"
        )
        embed_iframe: bool = Field(
            default=True,
            description="Embed the org-map inline as an iframe. If false, show a link only.",
        )

    def __init__(self):
        self.valves = self.Valves()

    def _render(self) -> str:
        url = self.valves.org_map_url
        parts = [
            "### NEXUS Org-Map",
            "",
            f"Live org ontology (personas, groups, KB access) served by ORKY:",
            "",
            f"**[Open Org-Map in a new tab]({url})**",
            "",
        ]
        if self.valves.embed_iframe:
            parts.append(
                f'<iframe src="{url}" width="100%" height="{self.valves.iframe_height}" '
                'style="border:1px solid var(--color-border,#27272a);border-radius:12px;" '
                'title="NEXUS Org-Map" loading="lazy"></iframe>'
            )
        return "\n".join(parts)

    async def action(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> Optional[dict]:
        """
        Called when the user clicks the Org-Map toolbar button.
        Emits a message with the link + iframe. Read-only; no model call.
        """
        if not self.valves.enabled:
            return None

        content = self._render()

        if __event_emitter__ is not None:
            await __event_emitter__(
                {
                    "type": "message",
                    "data": {"content": content},
                }
            )
            return None

        # Fallback for environments without an event emitter: append to body.
        return {"content": content}
