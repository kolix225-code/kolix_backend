# scripts/test_api.py
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
from app.main import app

async def run_integration_tests():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        print("\n=== 1. Test Health Check ===")
        res = await client.get("/health")
        print("Status:", res.status_code, "Body:", res.json())
        assert res.status_code == 200

        print("\n=== 2. Test Login Marchand ===")
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"identifier": "souleymane@kolix.ci", "password": "kolix2026!"}
        )
        print("Status:", login_res.status_code)
        login_data = login_res.json()
        print("Success:", login_data.get("success"), "Message:", login_data.get("message"))
        assert login_res.status_code == 200
        token = login_data["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        print("\n=== 3. Test Profil Connecté /auth/me ===")
        me_res = await client.get("/api/v1/auth/me", headers=headers)
        print("Me:", me_res.json().get("data"))
        assert me_res.status_code == 200

        print("\n=== 4. Test Vitrine Publique /public/store/elegance-tech ===")
        store_res = await client.get("/api/v1/public/store/elegance-tech")
        print("Store:", store_res.json().get("data", {}).get("name"), "Produits:", len(store_res.json().get("data", {}).get("products", [])))
        assert store_res.status_code == 200

        print("\n=== 5. Test Fiche Produit Publique /public/product/montre ===")
        prod_res = await client.get("/api/v1/public/product/montre-connectee-ultra-pro-series-9")
        print("Produit:", prod_res.json().get("data", {}).get("name"), "Prix:", prod_res.json().get("data", {}).get("price"))
        assert prod_res.status_code == 200

        print("\n=== 6. Test Passage de Commande COD /public/orders/checkout ===")
        order_res = await client.post(
            "/api/v1/public/orders/checkout",
            json={
                "shop_domain_or_slug": "elegance-tech",
                "client_name": "Fatou Bamba",
                "client_phone": "07 11 22 33 44",
                "city": "Abidjan - Marcory",
                "delivery_place": "Marcory Zone 4, Rue du Canal",
                "product_name": "Montre Connectée Ultra Pro Series 9",
                "pack_or_variant": "1x Montre Ultra Pro (Noir)",
                "amount": 18500.0,
                "payment_mode": "COD_CASH",
                "note": "Appeler 30 minutes avant"
            }
        )
        print("Status:", order_res.status_code)
        print("Commande créée:", order_res.json().get("data"))
        assert order_res.status_code == 201

        print("\n=== 7. Test Consultation Commandes Back-Office ===")
        orders_res = await client.get("/api/v1/orders", headers=headers)
        print("Total commandes:", len(orders_res.json().get("data", [])))
        assert orders_res.status_code == 200

        print("\n=== 8. Test Portefeuille Verrouillé /wallet/summary ===")
        w_res = await client.get("/api/v1/wallet/summary", headers=headers)
        w_data = w_res.json().get("data", {})
        print("Portefeuille:", w_data)
        assert w_res.status_code == 200
        assert w_data.get("is_digital_locked") is True
        print("Cadenas portefeuille numérique confirmé:", w_data.get("is_digital_locked"))

        print("\n=== 9. Test Espace Partenaire Verrouillé /affiliates/summary ===")
        aff_res = await client.get("/api/v1/affiliates/summary", headers=headers)
        aff_data = aff_res.json().get("data", {})
        print("Partenaire:", aff_data)
        assert aff_res.status_code == 200
        assert aff_data.get("is_locked") is True
        print("Cadenas espace partenaire confirmé:", aff_data.get("is_locked"))

        print("\n=== 10. Test Commande COD Format Kolix Page Produit ===")
        checkout_blendgo = await client.post(
            "/api/v1/public/orders/checkout",
            json={
                "shop_domain_or_slug": "elegance-tech",
                "customer": {
                    "name": "Aya Koné",
                    "phone": "07 12 34 56 78",
                    "city": "Abidjan",
                    "address": "Cocody Angré, pharmacie 8e tranche"
                },
                "product_name": "BlendGo – Mixeur portable 400 ml",
                "offer": "Pack 2 mixeurs",
                "quantity": 2,
                "total": 28900.0,
                "payment_mode": "cash_on_delivery",
                "note": "Couleur lavande si possible"
            }
        )
        print("Status BlendGo Checkout:", checkout_blendgo.status_code)
        print("Commande BlendGo reçue:", checkout_blendgo.json().get("data"))
        assert checkout_blendgo.status_code == 201

        print("\n=== 11. Test Création Produit avec Fiche Produit (Modèle Shopify) ===")
        new_prod_res = await client.post(
            "/api/v1/products",
            headers=headers,
            json={
                "name": "BlendGo Test 400ml",
                "category": "Électronique & Maison",
                "price": 15900.0,
                "price_old": 25000.0,
                "stock_quantity": 25,
                "stock_main": "Entrepôt Abidjan",
                "product_type": "Simple",
                "has_countdown": True,
                "fiche_produit": {
                    "headline": "BlendGo, le mixeur ultra-compact",
                    "leadSubtitle": "Des jus vitaminés en 30 secondes",
                    "stockUrgency": 14,
                    "countdownEnabled": True,
                    "offers": [
                        {"qty": 1, "label": "1 unité", "price": 15900},
                        {"qty": 2, "label": "Pack Duo", "price": 28900, "best": True}
                    ]
                }
            }
        )
        print("Status création produit:", new_prod_res.status_code)
        created_prod_data = new_prod_res.json().get("data", {})
        print("Produit créé avec slug:", created_prod_data.get("slug"))
        print("Fiche produit persistée:", created_prod_data.get("fiche_produit"))
        assert new_prod_res.status_code == 200
        assert created_prod_data.get("fiche_produit") is not None
        assert created_prod_data.get("fiche_produit", {}).get("headline") == "BlendGo, le mixeur ultra-compact"

        print("\n=== 12. Test Consultation Collaborateurs & Droits ===")
        users_res = await client.get("/api/v1/users/collaborators", headers=headers)
        print("Status liste collaborateurs:", users_res.status_code)
        print("Total collaborateurs:", len(users_res.json().get("data", [])))
        assert users_res.status_code == 200

        print("\n[TOUS LES TESTS D'INTÉGRATION SONT VALIDÉS AVEC SUCCÈS !]")

if __name__ == "__main__":
    asyncio.run(run_integration_tests())

