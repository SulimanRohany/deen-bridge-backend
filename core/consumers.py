import json
import re
from channels.generic.websocket import AsyncWebsocketConsumer

VALID_GROUP_RE = re.compile(r'^[A-Za-z0-9_.-]+$')

def _validate_segment(seg: str) -> str:
    if not isinstance(seg, str) or not VALID_GROUP_RE.match(seg):
        raise ValueError(
            "Invalid group segment: must be ASCII alphanumerics, '.', '-', or '_'."
        )
    return seg

def room_group_name(room_id: str) -> str:
    return f"room.{_validate_segment(room_id)}"

def peer_group_name(room_id: str, client_id: str) -> str:
    return f"room.{_validate_segment(room_id)}.peer.{_validate_segment(client_id)}"

class WebRTCSignalingConsumer(AsyncWebsocketConsumer):
    """
    Simple WebRTC signaling consumer for peer-to-peer connections:
      - Everyone joins room group: room.<room_id>
      - Each peer also joins personal group: room.<room_id>.peer.<clientId>
      - If message has `to`, send to that peer group; else broadcast to the room
    """

    async def connect(self):
        try:
            self.room_id = self.scope["url_route"]["kwargs"]["session_id"]
            self.room_group = room_group_name(self.room_id)
        except Exception as e:
            await self.close(code=4001)
            return

        self.client_id = None
        await self.accept()
        # Join room group immediately so we can receive broadcasts
        await self.channel_layer.group_add(self.room_group, self.channel_name)

    async def disconnect(self, code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group, self.channel_name)
        # Leave personal group (if registered)
        if self.client_id:
            await self.channel_layer.group_discard(
                peer_group_name(self.room_id, self.client_id), self.channel_name
            )

    async def receive(self, text_data):
        try:
            content = json.loads(text_data)
            msg_type = content.get("type")
            sender = content.get("from")
            target = content.get("to")

            if msg_type == "ready":
                # Register personal peer group once we know our clientId
                if sender and not self.client_id:
                    self.client_id = sender
                    await self.channel_layer.group_add(
                        peer_group_name(self.room_id, self.client_id), self.channel_name
                    )
                # Tell everyone I'm here (client ignores its own echo)
                await self.channel_layer.group_send(
                    self.room_group,
                    {"type": "signal.message", "payload": content}
                )
                return

            if msg_type in ("offer", "answer", "ice-candidate"):
                if target:
                    # Directed: send to that peer's personal group
                    await self.channel_layer.group_send(
                        peer_group_name(self.room_id, target),
                        {"type": "signal.message", "payload": content},
                    )
                else:
                    # No target → broadcast (safe; clients ignore self)
                    await self.channel_layer.group_send(
                        self.room_group,
                        {"type": "signal.message", "payload": content}
                    )
                return

            # Ignore unknown types silently
        except json.JSONDecodeError:
            pass
        except Exception:
            pass

    async def signal_message(self, event):
        try:
            await self.send(text_data=json.dumps(event["payload"]))
        except Exception:
            pass