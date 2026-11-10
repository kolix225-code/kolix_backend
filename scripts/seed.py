# scripts/seed.py
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timezone, date

# Ensure root directory is on python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User, Collaborator
from app.models.shop import Shop, StoreCustomization, StoreTemplate
from app.models.product import Product
from app.models.inventory import InventoryItem
from app.models.order import Order, OrderItem
from app.models.wallet import Wallet, PayoutAccount, WalletTransaction
from app.models.accounting import Charge
from app.models.client import Client
from app.models.settings import StoreSettings
from app.models.affiliate import Affiliate, AffiliateReferral

async def seed_data():
    async with AsyncSessionLocal() as db:
        # Check if already seeded
        check_user = await db.execute(select(User).where(User.email == "souleymane@kolix.ci"))
        if check_user.scalar_one_or_none():
            print("[INFO] La base de données est déjà initialisée avec le compte de démonstration.")
            return

        print("[START] Insertion des données initiales de démonstration...")

        # 1. Templates de boutique
        templates = [
            StoreTemplate(
                slug="aura_eclat",
                name="Aura Éclat",
                niche="Mode féminine",
                style="Épuré",
                price=0.0,
                price_label="Gratuit",
                is_free=True,
                accent_color="#6C4CF1",
                hero_text="Sublimez votre style avec nos collections exclusives",
                sub_text="Livraison express 24h à Abidjan et paiement à la livraison"
            ),
            StoreTemplate(
                slug="chic_homme",
                name="Chic & Prestige",
                niche="Mode masculine",
                style="Moderne",
                price=9000.0,
                price_label="15 USD",
                is_free=False,
                accent_color="#241D5E",
                hero_text="L'élégance masculine réinventée pour les professionnels",
                sub_text="Qualité premium, essayage et paiement à la réception"
            ),
            StoreTemplate(
                slug="tech_pro",
                name="Titan Gadgets",
                niche="Électronique et gadgets",
                style="Audacieux",
                price=0.0,
                price_label="Gratuit",
                is_free=True,
                accent_color="#FF6B00",
                hero_text="Dernières innovations technologiques certifiées",
                sub_text="Garantie 12 mois et livraison sécurisée à domicile"
            )
        ]
        db.add_all(templates)
        await db.flush()

        # 2. Utilisateur Marchand
        user = User(
            email="souleymane@kolix.ci",
            phone_dial="+225",
            phone_number="+2250700000001",
            password_hash=hash_password("kolix2026!"),
            full_name="Souleymane Sanogo",
            activity_type="Électronique & Mode",
            country="Côte d’Ivoire",
            role="Propriétaire",
            is_verified=True,
            is_active=True
        )
        db.add(user)
        await db.flush()

        # 3. Boutique principale
        shop = Shop(
            owner_id=user.id,
            name="Élégance & Tech Abidjan",
            slug="elegance-tech",
            domain="elegance-tech.kolix.shop",
            custom_domain="www.elegance-tech.ci",
            plan="Grow",
            orders_count=412,
            max_orders=1500,
            status="En ligne",
            is_active=True,
            accent_color="#6C4CF1"
        )
        db.add(shop)
        await db.flush()

        # 4. Personnalisation & Thème
        custom = StoreCustomization(
            shop_id=shop.id,
            template_id="aura_eclat",
            primary_color="#6C4CF1",
            sections=[
                {"id": "hero", "label": "Bannière & Slogan", "enabled": True, "order": 1},
                {"id": "featured", "label": "Produit vedette", "enabled": True, "order": 2},
                {"id": "reviews", "label": "Avis clients vérifiés", "enabled": True, "order": 3},
                {"id": "form", "label": "Formulaire de commande COD", "enabled": True, "order": 4},
            ]
        )
        db.add(custom)

        # 5. Collaborateurs
        collabs = [
            Collaborator(
                shop_id=shop.id,
                name="Amadou Koné",
                phone="07 08 22 11 00",
                email="amadou.kone@kolix.ci",
                role="Gestionnaire de commandes",
                status="Actif",
                permissions=["Accueil", "Produits", "Commandes", "Stock", "Client"]
            ),
            Collaborator(
                shop_id=shop.id,
                name="Koffi Michel",
                phone="05 44 33 22 11",
                email="koffi.livreur@kolix.ci",
                role="Livreur",
                status="Actif",
                permissions=["Commandes"]
            )
        ]
        db.add_all(collabs)

        # 6. Produits
        watch = Product(
            shop_id=shop.id,
            name="Montre Connectée Ultra Pro Series 9",
            slug="montre-connectee-ultra-pro-series-9",
            category="Électronique et gadgets",
            price=18500.0,
            price_old=28500.0,
            stock_quantity=24,
            stock_main="Entrepôt Cocody",
            stock_rest="Showroom Plateau",
            status="Actif",
            has_countdown=True,
            description="Écran AMOLED Ultra HD 2.02, appels Bluetooth, suivi de santé 24/7 et résistance IP68.",
            images=[
                "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?auto=format&fit=crop&w=900&q=80",
                "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?auto=format&fit=crop&w=900&q=80"
            ]
        )
        serum = Product(
            shop_id=shop.id,
            name="Sérum Éclat Pur Vitamine C 30ml",
            slug="serum-eclat-pur-vitamine-c-30ml",
            category="Beauté, cosmétiques et soins",
            price=12000.0,
            price_old=16500.0,
            stock_quantity=45,
            stock_main="Entrepôt Cocody",
            stock_rest="Rayon vitrine",
            status="Actif",
            has_countdown=False,
            description="Anti-taches puissant pour un teint lumineux dès 14 jours.",
            images=[
                "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=900&q=80"
            ]
        )
        db.add_all([watch, serum])
        await db.flush()

        # 7. Inventaire
        inv_watch = InventoryItem(
            shop_id=shop.id,
            product_id=watch.id,
            num="PRD-WATCH-01",
            qty_initial=50,
            qty_sold=26,
            qty_remaining=24,
            threshold=7,
            unit_cost=8500.0,
            status="Optimal"
        )
        inv_serum = InventoryItem(
            shop_id=shop.id,
            product_id=serum.id,
            num="PRD-SERUM-02",
            qty_initial=100,
            qty_sold=55,
            qty_remaining=45,
            threshold=10,
            unit_cost=5000.0,
            status="Optimal"
        )
        db.add_all([inv_watch, inv_serum])

        # 8. Commandes COD
        orders = [
            Order(
                id="KX-1048",
                shop_id=shop.id,
                client_name="Aya Kouassi",
                client_phone="07 08 12 34 48",
                city="Cocody",
                delivery_place="Cocody Angré 8e tranche, carrefour pharmacie",
                total_amount=18500.0,
                status="En cours",
                payment_mode="COD_MOMO",
                note="Livrer après 17h, appeler avant.",
                qr_payload="KOLIX-PAY:KX-1048:18500:XOF:AYA-KOUASSI"
            ),
            Order(
                id="KX-1049",
                shop_id=shop.id,
                client_name="Moussa Traoré",
                client_phone="05 55 44 33 22",
                city="Yopougon",
                delivery_place="Yopougon Selmer, face station Total",
                total_amount=32000.0,
                status="Livrée",
                payment_mode="COD_CASH",
                paid_at=datetime.now(timezone.utc),
                note="Prévoir la monnaie sur 40 000 F",
                qr_payload="KOLIX-PAY:KX-1049:32000:XOF:MOUSSA-TRAORE"
            )
        ]
        db.add_all(orders)
        await db.flush()

        item1 = OrderItem(order_id="KX-1048", product_id=watch.id, product_name=watch.name, variant_label="Noir Sidéral", quantity=1, unit_price=18500.0)
        item2 = OrderItem(order_id="KX-1049", product_id=watch.id, product_name=watch.name, variant_label="Pack Duo", quantity=1, unit_price=32000.0)
        db.add_all([item1, item2])

        # 9. Portefeuille & Comptes
        wallet = Wallet(
            shop_id=shop.id,
            digital_balance=185000.0,
            cash_balance=32000.0,
            pending_balance=18500.0,
            withdrawn_month=450000.0,
            kolix_commission=12500.0
        )
        db.add(wallet)
        await db.flush()

        payout_acc = PayoutAccount(
            wallet_id=wallet.id,
            name="Souleymane Sanogo Wave",
            num="07 00 00 00 01",
            provider="Wave",
            is_default=True
        )
        db.add(payout_acc)

        trx = WalletTransaction(
            wallet_id=wallet.id,
            ref="TRX-1049",
            who="Moussa Traoré",
            mode="Espèces",
            status="Validé",
            amount=32000.0,
            is_credit=True,
            is_cash=True,
            order_id="KX-1049"
        )
        db.add(trx)

        # 10. Charges Comptables
        charges = [
            Charge(shop_id=shop.id, date=date(2026, 10, 15), label="Campagne TikTok Ads Montres", category="Publicité", payment_mode="Mobile Money", amount=45000.0),
            Charge(shop_id=shop.id, date=date(2026, 10, 18), label="Frais de livraison courses Abidjan", category="Transport et livraison", payment_mode="Espèces", amount=18000.0),
            Charge(shop_id=shop.id, date=date(2026, 10, 20), label="Achat stock fournisseur 50x Montres", category="Achat de stock", payment_mode="Virement bancaire", amount=250000.0),
        ]
        db.add_all(charges)

        # 11. Paramètres & Formulaire COD
        settings = StoreSettings(
            shop_id=shop.id,
            slogan="L'élégance à votre poignet, la technologie à votre service",
            currency="FCFA (XOF)",
            phone="07 00 00 00 01",
            email="contact@elegance-tech.ci",
            address="Cocody Angré 8e Tranche, Abidjan"
        )
        db.add(settings)

        # 12. Affiliation
        aff = Affiliate(
            user_id=user.id,
            affiliate_code="KXSOUL10",
            affiliate_slug="souleymane",
            available_balance=145000.0,
            total_earned=536000.0
        )
        db.add(aff)

        await db.commit()
        print("[SUCCESS] Base de données initialisée avec succès avec les données de démonstration Kolix !")

if __name__ == "__main__":
    asyncio.run(seed_data())

