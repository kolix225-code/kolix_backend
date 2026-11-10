# app/api/v1/endpoints/users.py
import uuid
from typing import Annotated, List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import PermissionChecker, get_current_shop, get_current_user
from app.core.exceptions import NotFoundException
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
    """Inviter un nouveau collaborateur avec assignation des modules autorisés."""
    collab = Collaborator(
        shop_id=shop.id,
        name=data.name,
        phone=data.phone,
        email=data.email,
        role=data.role,
        status="Actif",
        permissions=data.permissions,
        is_owner=False
    )
    db.add(collab)
    await db.commit()
    await db.refresh(collab)
    return StandardResponse(message="Collaborateur ajouté avec succès.", data=CollaboratorResponse.model_validate(collab))

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
    """Mettre à jour le rôle ou les permissions d'un collaborateur."""
    stmt = select(Collaborator).where(Collaborator.id == id, Collaborator.shop_id == shop.id)
    res = await db.execute(stmt)
    collab = res.scalar_one_or_none()
    if not collab:
        raise NotFoundException("Collaborateur", str(id))

    if data.name is not None:
        collab.name = data.name
    if data.phone is not None:
        collab.phone = data.phone
    if data.role is not None:
        collab.role = data.role
    if data.status is not None:
        collab.status = data.status
    if data.permissions is not None:
        collab.permissions = data.permissions

    await db.commit()
    await db.refresh(collab)
    return StandardResponse(message="Permissions mises à jour.", data=CollaboratorResponse.model_validate(collab))

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

