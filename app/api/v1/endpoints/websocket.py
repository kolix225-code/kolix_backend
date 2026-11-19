# app/api/v1/endpoints/websocket.py
import json
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.ws_manager import ws_manager
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["WebSocket Temps Réel"])

@router.websocket("/ws/{shop_id}")
async def websocket_shop_endpoint(
    websocket: WebSocket,
    shop_id: str,
    token: str | None = Query(None)
):
    """Endpoint WebSocket temps réel par boutique.
    Permet à tous les onglets du tableau de bord d'être notifiés instantanément des changements
    (nouvelles commandes, changements de statut, stock, comptabilité, utilisateurs).
    """
    await ws_manager.connect(websocket, shop_id)
    try:
        # Envoyer confirmation de connexion
        await websocket.send_text(json.dumps({
            "event": "CONNECTED",
            "data": {"shop_id": shop_id},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }))

        while True:
            # Écouter les pings de maintien de connexion (heartbeat)
            raw_msg = await websocket.receive_text()
            try:
                msg = json.loads(raw_msg)
                if msg.get("type") == "ping" or msg.get("event") == "ping" or raw_msg == "ping":
                    await websocket.send_text(json.dumps({
                        "event": "PONG",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }))
            except Exception:
                if raw_msg == "ping":
                    await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, shop_id)
    except Exception as e:
        logger.warning("Erreur inattendue WebSocket", shop_id=shop_id, error=str(e))
        ws_manager.disconnect(websocket, shop_id)

