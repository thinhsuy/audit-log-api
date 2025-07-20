from fastapi import WebSocket
from broadcaster import Broadcast as LibBroadcast
from core.services.base import AppService
from typing import List, Dict, Tuple
import asyncio
import json
import gzip

class ConnectionManager(AppService):
    def __init__(self) -> WebSocket:
        self.channels: Dict[str, List[Tuple[WebSocket, str]]] = {}

    async def connect(self, websocket: WebSocket, session_id: str, user_id: str):
        """
            Generate connections pool that could control the number of connection
            to one specific channel/tenant_id
        """
        await websocket.accept()
        print(f"WebSocket connected: {websocket.client}")
        if session_id not in self.channels:
            self.channels[session_id] = []
        self.channels[session_id].append((websocket, user_id))

    def disconnect(self, websocket: WebSocket, session_id: str):
        """ Remove a WebSocket connection from the session """
        if session_id in self.channels:
            self.channels[session_id] = [
                (ws, user_id)
                for ws, user_id in self.channels[session_id]
                if ws != websocket
            ]
            if not self.channels[session_id]:
                del self.channels[session_id]

        try:
            websocket.close()
        except Exception as e:
            print(f"Error closing WebSocket: {e}")


    async def broadcast_message(self, message: str, session_id: str):
        """ Broadcast message to all clients in a specific room/session """
        if session_id in self.channels:
            disconnected_clients = []
            for websocket, _ in self.channels[session_id]:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    print(f"Error sending message to WebSocket: {e}")
                    disconnected_clients.append(websocket)

            self.channels[session_id] = [
                (ws, user_id)
                for ws, user_id in self.channels[session_id]
                if ws not in disconnected_clients
            ]
            if not self.channels[session_id]:
                del self.channels[session_id]

    def get_user_ids(self, session_id: str) -> List[str]:
        """ Get the list of user IDs connected to a channel """
        if session_id in self.channels:
            return [user_id for _, user_id in self.channels[session_id]]
        return []


class WebSocketSerivce(AppService):
    def __init__(self, storage: str = "memory://") -> None:
        self.broadcast = LibBroadcast(storage)
        self.active_listeners = set()

    async def connect(self):
        await self.broadcast.connect()

    async def disconnect(self):
        await self.broadcast.disconnect()

    async def listen_to_channel(self, manager: ConnectionManager, session_id: str):
        """ Listen for broadcast messages and send them to all connected clients """
        try:
            async with self.broadcast.subscribe(channel=session_id) as subscriber:
                async for event in subscriber:
                    try:
                        await manager.broadcast_message(event.message, session_id)
                    except Exception as e:
                        print(f"Error broadcasting message for session {session_id}: {e}")
        except Exception as e:
            print(f"Error in listen_to_channel for session {session_id}: {e}")
        finally:
            # Ensure the listener is removed from the active list on error or completion
            self.active_listeners.discard(session_id)

    def create_listener(self, manager: ConnectionManager, session_id: str):
        """ Create a listener for each channel, ensuring no duplicate listeners """
        if session_id in self.active_listeners:
            return

        if session_id not in manager.channels or not manager.channels[session_id]:
            return
        self.active_listeners.add(session_id)
        task = asyncio.create_task(self.listen_to_channel(manager, session_id))

        def cleanup(task):
            self.active_listeners.discard(session_id)

        task.add_done_callback(cleanup)

    async def receive_message(self, websocket: WebSocket):
        return await websocket.receive_text()

    async def send_message(self, session_id: str, message_package: dict):
        """ Send a message to the broadcast channel """
        compressed_data = gzip.compress(json.dumps(message_package).encode('utf-8'))
        for _ in range(3):  # Retry up to 3 times
            try:
                await self.broadcast.publish(channel=session_id, message=compressed_data)
                break
            except Exception as e:
                print(f"Error publishing message to session {session_id}: {e}")
                await asyncio.sleep(0.5)
        else:
            print(f"Failed to publish message to session {session_id} after retries")

    async def send_string(self, session_id: str, message: str):
        """ Send a message to the broadcast channel """
        await self.broadcast.publish(channel=session_id, message=message)


WS_MANAGER = ConnectionManager()
WS_SERVICE = WebSocketSerivce()