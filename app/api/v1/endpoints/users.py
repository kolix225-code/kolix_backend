# app/api/v1/endpoints/users.py
import uuid
from typing import Annotated, List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import PermissionChecker, get_current_shop, get_current_user
from app.core.exceptions import NotFoundException
from app.core.security import hash_password
from app.models.shop import Shop
from app.models.user import Collaborator, User
from app.schemas.common import StandardResponse
from app.schemas.user import CollaboratorCreate, CollaboratorResponse, CollaboratorUpdate

router = APIRouter(prefix="/users", tags=["Utilisateurs & Équipe"])

@router.get(
    "/collaborators",
    response_model=StandardResponse[List[CollaboratorResponse]],
    dependencies=[Depends(PermissionChecker("Utilisateurs"))]
)
async def list_collaborators(
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Liste tous les membres d'équipe de la boutique courante."""
    stmt = select(Collaborator).where(Collaborator.shop_id == shop.id, Collaborator.is_deleted == False)
    res = await db.execute(stmt)
    collaborators = res.scalars().all()
    return StandardResponse(data=[CollaboratorResponse.model_validate(c) for c in collaborators])

@router.post(
    "/collaborators",
    response_model=StandardResponse[CollaboratorResponse],
    dependencies=[Depends(PermissionChecker("Utilisateurs"))]
)
async def add_collaborator(
    data: CollaboratorCreate,
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Inviter un nouveau collaborateur avec assignation des accès de connexion et modules autorisés."""
    import random
    import re
    from sqlalchemy import or_

    clean_email = data.email.strip().lower()
    raw_phone = re.sub(r"[^\d]", "", data.phone)
    if raw_phone.startswith("225"):
        clean_phone = raw_phone[3:]
    else:
        clean_phone = raw_phone
    if not clean_phone:
        clean_phone = f"07{random.randint(10000000, 99999999)}"

    collab_pwd = data.password.strip() if (data.password and len(data.password.strip()) >= 4) else "Kolix@2026!"

    # 1. Vérifier si un compte User existe déjà avec cet email ou ce téléphone
    stmt_u = select(User).where(
        or_(
            User.email.ilike(clean_email),
            User.phone_number == clean_phone,
            User.phone_number == f"+225{clean_phone}",
            User.phone_number == f"225{clean_phone}"
        )
    )
    u_res = await db.execute(stmt_u)
    existing_user = u_res.scalars().first()

    if not existing_user:
        new_u = User(
            email=clean_email,
            phone_dial="+225",
            phone_number=clean_phone,
            password_hash=hash_password(collab_pwd),
            full_name=data.name.strip(),
            role=data.role,
            is_verified=True,
            is_active=True
        )
        db.add(new_u)
        await db.flush()
    else:
        existing_user.password_hash = hash_password(collab_pwd)
        existing_user.full_name = data.name.strip()
        existing_user.role = data.role
        existing_user.is_verified = True
        existing_user.is_active = True

    # 2. Vérifier si une fiche Collaborator existe déjà pour cette boutique
    stmt_c = select(Collaborator).where(
        Collaborator.shop_id == shop.id,
        or_(
            Collaborator.email.ilike(clean_email),
            Collaborator.phone == clean_phone
        )
    )
    c_res = await db.execute(stmt_c)
    collab = c_res.scalars().first()

    if collab:
        collab.name = data.name.strip()
        collab.phone = clean_phone
        collab.email = clean_email
        collab.role = data.role
        collab.status = "Actif"
        collab.permissions = data.permissions
        collab.is_deleted = False
    else:
        collab = Collaborator(
            shop_id=shop.id,
            name=data.name.strip(),
            phone=clean_phone,
            email=clean_email,
            role=data.role,
            status="Actif",
            permissions=data.permissions,
            is_owner=False
        )
        db.add(collab)

    await db.commit()
    await db.refresh(collab)
    return StandardResponse(
        message=f"Collaborateur {collab.name} ajouté avec succès. Accès de connexion activés.",
        data=CollaboratorResponse.model_validate(collab)
    )

@router.put(
    "/collaborators/{id}",
    response_model=StandardResponse[CollaboratorResponse],
    dependencies=[Depends(PermissionChecker("Utilisateurs"))]
)
async def update_collaborator(
    id: uuid.UUID,
    data: CollaboratorUpdate,
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Mettre à jour le rôle, mot de passe ou les permissions d'un collaborateur."""
    import re
    from sqlalchemy import or_

    stmt = select(Collaborator).where(Collaborator.id == id, Collaborator.shop_id == shop.id)
    res = await db.execute(stmt)
    collab = res.scalar_one_or_none()
    if not collab:
        raise NotFoundException("Collaborateur", str(id))

    old_email = collab.email
    old_phone = collab.phone

    if data.name is not None:
        collab.name = data.name.strip()
    if data.email is not None:
        collab.email = data.email.strip().lower()
    if data.phone is not None:
        raw_p = re.sub(r"[^\d]", "", data.phone)
        collab.phone = raw_p[3:] if raw_p.startswith("225") else raw_p
    if data.role is not None:
        collab.role = data.role
    if data.status is not None:
        collab.status = data.status
    if data.permissions is not None:
        collab.permissions = data.permissions

    # Synchroniser le compte User correspondant
    stmt_u = select(User).where(
        or_(
            User.email.ilike(old_email),
            User.email.ilike(collab.email),
            User.phone_number == old_phone,
            User.phone_number == collab.phone
        )
    )
    u_res = await db.execute(stmt_u)
    u = u_res.scalars().first()
    if u:
        if data.name is not None:
            u.full_name = data.name.strip()
        if data.role is not None:
            u.role = data.role
        if data.status is not None:
            u.is_active = (data.status != "Suspendu")
        if data.password and len(data.password.strip()) >= 4:
            u.password_hash = hash_password(data.password.strip())
        u.is_verified = True

    await db.commit()
    await db.refresh(collab)
    return StandardResponse(message="Permissions et accès mis à jour.", data=CollaboratorResponse.model_validate(collab))

@router.delete(
    "/collaborators/{id}",
    response_model=StandardResponse[None],
    dependencies=[Depends(PermissionChecker("Utilisateurs"))]
)
async def delete_collaborator(
    id: uuid.UUID,
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Supprimer un collaborateur."""
    stmt = select(Collaborator).where(Collaborator.id == id, Collaborator.shop_id == shop.id)
    res = await db.execute(stmt)
    collab = res.scalar_one_or_none()
    if not collab:
        raise NotFoundException("Collaborateur", str(id))

    collab.is_deleted = True
    await db.commit()
    return StandardResponse(message="Collaborateur retiré de la boutique.")

