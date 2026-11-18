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
    clean_email = data.email.strip().lower()
    clean_phone = data.phone.strip().replace(" ", "")
    stmt_u = select(User).where((User.email == clean_email) | (User.phone_number == clean_phone))
    u_res = await db.execute(stmt_u)
    existing_user = u_res.scalar_one_or_none()

    collab_pwd = data.password if (data.password and len(data.password) >= 6) else "kolix2026!"
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
        if data.password and len(data.password) >= 6:
            existing_user.password_hash = hash_password(data.password)

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
    return StandardResponse(message=f"Collaborateur {collab.name} ajouté avec succès. Accès de connexion activés.", data=CollaboratorResponse.model_validate(collab))

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
    stmt = select(Collaborator).where(Collaborator.id == id, Collaborator.shop_id == shop.id)
    res = await db.execute(stmt)
    collab = res.scalar_one_or_none()
    if not collab:
        raise NotFoundException("Collaborateur", str(id))

    if data.name is not None:
        collab.name = data.name.strip()
    if data.phone is not None:
        collab.phone = data.phone.strip().replace(" ", "")
    if data.role is not None:
        collab.role = data.role
    if data.status is not None:
        collab.status = data.status
    if data.permissions is not None:
        collab.permissions = data.permissions

    # Si un nouveau mot de passe est transmis, mettre à jour le compte User correspondant
    if data.password and len(data.password) >= 6:
        stmt_u = select(User).where((User.email == collab.email) | (User.phone_number == collab.phone))
        u_res = await db.execute(stmt_u)
        u = u_res.scalar_one_or_none()
        if u:
            u.password_hash = hash_password(data.password)

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

