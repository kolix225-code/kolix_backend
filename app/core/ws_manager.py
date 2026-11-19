# app/core/ws_manager.py
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Set
from fastapi import WebSocket
import structlog

logger = structlog.get_logger(__name__)

class ConnectionManager:
    """Gestionnaire de connexions WebSocket en temps réel par boutique (Room-based)."""
    
    def __init__(self):
        # Dictionnaire associant shop_id (str) à un ensemble de WebSockets connectés
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, shop_id: str):
        await websocket.accept()
        if shop_id not in self.active_connections:
            self.active_connections[shop_id] = set()
        self.active_connections[shop_id].add(websocket)
        logger.info("WebSocket client connecté", shop_id=shop_id, total_clients=len(self.active_connections[shop_id]))

    def disconnect(self, websocket: WebSocket, shop_id: str):
        if shop_id in self.active_connections:
            self.active_connections[shop_id].discard(websocket)
            if len(self.active_connections[shop_id]) == 0:
                del self.active_connections[shop_id]
        logger.info("WebSocket client déconnecté", shop_id=shop_id)

    async def broadcast_to_shop(self, shop_id: str | uuid.UUID, event: str, data: dict = None):
        """Diffuser un événement en temps réel à tous les écrans ouverts de la boutique donnée."""
        sid = str(shop_id)
        if sid not in self.active_connections or not self.active_connections[sid]:
            return

        payload = {
            "event": event,
            "data": data or {},
            "shop_id": sid,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        message_str = json.dumps(payload)
        
        stale_connections = set()
        for connection in list(self.active_connections[sid]):
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.warning("Échec envoi WebSocket", error=str(e), shop_id=sid)
                stale_connections.add(connection)

        # Nettoyage automatique des sockets rompus
        for dead_ws in stale_connections:
            self.disconnect(dead_ws, sid)

    async def broadcast_all(self, event: str, data: dict = None):
        """Diffuser un message global à toutes les boutiques connectées."""
        for sid in list(self.active_connections.keys()):
            await self.broadcast_to_shop(sid, event, data)

ws_manager = ConnectionManager()

