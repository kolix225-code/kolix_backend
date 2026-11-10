# app/services/ai_service.py
import json
from typing import AsyncGenerator, List
from litellm import acompletion
from app.core.config import settings

SYSTEM_PROMPT = """
Tu es l'assistant exécutif et stratège officiel de Kolix, le système d'exploitation e-commerce et de paiement à la livraison (COD) pour l'Afrique francophone (Côte d'Ivoire, Sénégal, Mali, etc.).
Tu t'adresses à des commerçants ambitieux.
Tes réponses sont concises, pratiques, expertes en marketing digital (Meta/TikTok Ads), gestion rigoureuse de trésorerie et réduction des taux de retour livreur.
Exprime les montants en FCFA (XOF).
"""

class AiService:
    @staticmethod
    async def generate_response(messages: List[dict], shop_context: dict | None = None) -> str:
        ctx_str = f"\nContexte boutique : {json.dumps(shop_context)}" if shop_context else ""
        augmented = [
            {"role": "system", "content": f"{SYSTEM_PROMPT}{ctx_str}"},
            *messages
        ]

        if not settings.GEMINI_API_KEY:
            # Intelligent fallback response for local development without API key
            user_msg = messages[-1]["content"] if messages else ""
            return (
                f"Bonjour ! En tant qu'assistant Kolix AI, voici mon analyse pour votre boutique :\n\n"
                f"Concernant votre demande : « {user_msg} »\n\n"
                f"1. **Taux de livraison COD** : Assurez-vous d'appeler les clients dans les 15 minutes suivant la commande pour confirmer l'adresse.\n"
                f"2. **Gestion de stock** : Surveillez vos produits à forte rotation (ex: Sangles, Montres) pour anticiper les ruptures.\n"
                f"3. **Campagnes WhatsApp** : Relancez vos clients inactifs depuis plus de 30 jours avec une offre personnalisée."
            )

        try:
            resp = await acompletion(
                model=settings.DEFAULT_LLM_MODEL,
                messages=augmented,
                api_key=settings.GEMINI_API_KEY,
                temperature=0.7,
                max_tokens=800
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            return f"Service IA temporairement indisponible ({str(e)}). Veuillez vérifier votre clé API dans le fichier .env."

