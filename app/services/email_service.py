# app/services/email_service.py
from typing import Optional
import httpx
import structlog
from app.core.config import settings

logger = structlog.get_logger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

class EmailService:
    @staticmethod
    async def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        to_name: Optional[str] = None
    ) -> bool:
        """
        Envoie un email transactionnel via l'API REST de Brevo (Sendinblue).
        Si BREVO_API_KEY n'est pas renseignée, simule l'envoi en journalisant le message.
        """
        if not settings.BREVO_API_KEY or settings.BREVO_API_KEY.strip() == "":
            logger.warning(
                "[BREVO EMAIL SIMULATION] Clé API non configurée. L'email ne sera pas envoyé dans le monde réel.",
                to_email=to_email,
                subject=subject,
            )
            return True

        sender_email = settings.BREVO_SENDER_EMAIL or "noreply@kolix.ci"
        sender_name = settings.BREVO_SENDER_NAME or "Kolix"

        payload = {
            "sender": {
                "name": sender_name,
                "email": sender_email
            },
            "to": [
                {
                    "email": to_email,
                    "name": to_name or to_email
                }
            ],
            "subject": subject,
            "htmlContent": html_content
        }

        headers = {
            "accept": "application/json",
            "api-key": settings.BREVO_API_KEY.strip(),
            "content-type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(BREVO_API_URL, json=payload, headers=headers)
                if response.status_code in (200, 201, 202):
                    logger.info(
                        "Email Brevo envoyé avec succès",
                        to=to_email,
                        status_code=response.status_code,
                        response=response.json()
                    )
                    return True
                else:
                    logger.error(
                        "Échec de l'envoi email Brevo",
                        status_code=response.status_code,
                        body=response.text,
                        to=to_email
                    )
                    return False
        except Exception as e:
            logger.error("Exception lors de l'appel API Brevo", error=str(e), to=to_email)
            return False

    @classmethod
    async def send_otp_email(cls, to_email: str, to_name: str, otp_code: str) -> bool:
        """
        Envoie le code OTP de confirmation de compte par email via Brevo.
        """
        subject = f"Votre code de confirmation Kolix : {otp_code}"
        expire_minutes = settings.OTP_EXPIRE_MINUTES

        html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Vérification de votre compte Kolix</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f5f7; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f4f5f7; padding: 40px 10px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width: 520px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.06); border: 1px solid #e2e8f0;" cellspacing="0" cellpadding="0">
          
          <!-- En-tête avec marque -->
          <tr>
            <td style="background: linear-gradient(135deg, #241D5E 0%, #6C4CF1 100%); padding: 36px 32px; text-align: center;">
              <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 800; letter-spacing: -0.5px;">KOLIX</h1>
              <p style="margin: 6px 0 0; color: #e0e7ff; font-size: 14px; font-weight: 500;">Plateforme E-commerce & COD Nouvelle Génération</p>
            </td>
          </tr>

          <!-- Contenu principal -->
          <tr>
            <td style="padding: 36px 32px;">
              <h2 style="margin: 0 0 16px; font-size: 20px; font-weight: 700; color: #0f172a;">Bonjour {to_name or 'cher e-commerçant'},</h2>
              <p style="margin: 0 0 24px; font-size: 15px; line-height: 1.6; color: #475569;">
                Bienvenue sur <strong>Kolix</strong> ! Pour finaliser la création de votre compte et activer votre boutique en ligne, veuillez saisir le code de sécurité temporaire ci-dessous :
              </p>

              <!-- Bloc OTP -->
              <div style="background-color: #f8fafc; border: 2px dashed #6C4CF1; border-radius: 12px; padding: 24px; text-align: center; margin: 28px 0;">
                <span style="display: block; font-size: 12px; font-weight: 700; color: #6C4CF1; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px;">Votre Code de Vérification</span>
                <span style="font-family: 'Courier New', Courier, monospace; font-size: 38px; font-weight: 800; letter-spacing: 8px; color: #1e1b4b; display: inline-block;">{otp_code}</span>
              </div>

              <!-- Information d'expiration -->
              <p style="margin: 0 0 20px; font-size: 13px; line-height: 1.5; color: #64748b; text-align: center;">
                ⏱ Ce code est valable pendant <strong>{expire_minutes} minutes</strong>.<br>
                Si vous n'êtes pas à l'origine de cette demande, vous pouvez ignorer cet email en toute sécurité.
              </p>

              <hr style="border: none; border-top: 1px solid #f1f5f9; margin: 28px 0 20px;">

              <!-- Conseil sécurité -->
              <p style="margin: 0; font-size: 12px; line-height: 1.5; color: #94a3b8; text-align: center;">
                🔒 Ne communiquez jamais ce code à un tiers. Aucun membre de l'équipe Kolix ne vous le demandera.
              </p>
            </td>
          </tr>

          <!-- Pied de page -->
          <tr>
            <td style="background-color: #f8fafc; padding: 20px 32px; text-align: center; border-top: 1px solid #f1f5f9;">
              <p style="margin: 0; font-size: 12px; color: #94a3b8;">
                © 2026 Kolix COD. Tous droits réservés.<br>
                <a href="https://kolix-kohl.vercel.app" style="color: #6C4CF1; text-decoration: none; font-weight: 600;">Accéder à Kolix</a>
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
        return await cls.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            to_name=to_name
        )

