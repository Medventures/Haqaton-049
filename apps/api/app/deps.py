from sqlalchemy.orm import Session

from app.errors import not_found
from app.models import Family, User


def get_family_for_curator(db: Session, family_id: int, user: User) -> Family:
    family = db.get(Family, family_id)
    if family is None or family.curator_id != user.id:
        raise not_found("Семья не найдена")
    return family


def get_own_family_for_parent(db: Session, user: User) -> Family:
    family = db.query(Family).filter(Family.parent_id == user.id).one_or_none()
    if family is None:
        raise not_found("Семья не найдена")
    return family


def get_family_for_parent(db: Session, family_id: int, user: User) -> Family:
    family = db.get(Family, family_id)
    if family is None or family.parent_id != user.id:
        raise not_found("Семья не найдена")
    return family
