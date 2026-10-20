"""
Service pour les activités - CRUD et opérations métier
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from data.models import Activity
from typing import List, Optional
import uuid

class ActivityService:
    """Gestion complète des activités"""
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Activity]:
        """Récupère tous les activités"""
        return db.query(Activity).filter(Activity.is_active == True).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_id(db: Session, activity_id: str) -> Optional[Activity]:
        """Récupère une activité par son ID"""
        return db.query(Activity).filter(Activity.id == activity_id).first()
    
    @staticmethod
    def create(db: Session, activity_data: dict) -> Activity:
        """Crée une nouvelle activité"""
        activity = Activity(**activity_data)
        activity.id = str(uuid.uuid4())
        db.add(activity)
        db.commit()
        db.refresh(activity)
        return activity
    
    @staticmethod
    def update(db: Session, activity_id: str, activity_data: dict) -> Optional[Activity]:
        """Met à jour une activité"""
        activity = ActivityService.get_by_id(db, activity_id)
        if not activity:
            return None
        
        for key, value in activity_data.items():
            setattr(activity, key, value)
        
        db.commit()
        db.refresh(activity)
        return activity
    
    @staticmethod
    def delete(db: Session, activity_id: str) -> bool:
        """Supprime une activité (soft delete)"""
        activity = ActivityService.get_by_id(db, activity_id)
        if not activity:
            return False
        
        activity.is_active = False
        db.commit()
        return True
    
    @staticmethod
    def filter_activities(
        db: Session,
        categories: List[str] = None,
        budget_min: int = None,
        budget_max: int = None,
        duration_max: int = None,
        distance_max: int = None,
        min_rating: float = None,
        public_type: str = None,
        effort_level: str = None,
        effort_level: str = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Activity]:
        """Filtre les activités selon plusieurs critères"""
        
        query = db.query(Activity).filter(Activity.is_active == True)
        
        if categories:
            query = query.filter(Activity.category.in_(categories))
        
        if budget_min is not None:
            query = query.filter(Activity.price_mad >= budget_min)
        
        if budget_max is not None:
            query = query.filter(Activity.price_mad <= budget_max)
        
        if duration_max is not None:
            query = query.filter(Activity.duration_minutes <= duration_max)
        
        if distance_max is not None:
            query = query.filter(Activity.distance_from_center_km <= distance_max)
        
        if min_rating is not None:
            query = query.filter(Activity.avg_rating >= min_rating)
        
        if public_type and public_type != "Tous":
            query = query.filter(
                or_(
                    Activity.public_type == public_type,
                    Activity.public_type == "Tous"
                )
            )
        
        if effort_level:
            query = query.filter(Activity.effort_level == effort_level)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def search(db: Session, query_str: str, skip: int = 0, limit: int = 100) -> List[Activity]:
        """Recherche des activités par texte libre"""
        search_term = f"%{query_str}%"
        
        return db.query(Activity).filter(
            Activity.is_active == True,
            or_(
                Activity.name_fr.ilike(search_term),
                Activity.description_short_fr.ilike(search_term),
                Activity.category.ilike(search_term)
            )
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_top_rated(db: Session, limit: int = 10) -> List[Activity]:
        """Récupère les activités les mieux notées"""
        return db.query(Activity).filter(
            Activity.is_active == True,
            Activity.review_count > 0
        ).order_by(Activity.avg_rating.desc()).limit(limit).all()
    
    @staticmethod
    def get_by_category(db: Session, category: str, skip: int = 0, limit: int = 100) -> List[Activity]:
        """Récupère les activités d'une catégorie"""
        return db.query(Activity).filter(
            Activity.is_active == True,
            Activity.category == category
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_categories(db: Session) -> List[str]:
        """Récupère la liste unique des catégories"""
        categories = db.query(Activity.category).filter(
            Activity.is_active == True
        ).distinct().all()
        return [cat[0] for cat in categories if cat[0]]
    
    @staticmethod
    def update_rating(db: Session, activity_id: str):
        """Met à jour la note moyenne d'une activité basée sur les avis"""
        from data.models import Review
        
        activity = ActivityService.get_by_id(db, activity_id)
        if not activity:
            return
        
        reviews = db.query(Review).filter(
            Review.activity_id == activity_id,
            Review.verified_badge == True
        ).all()
        
        if reviews:
            avg_rating = sum(r.rating for r in reviews) / len(reviews)
            activity.avg_rating = round(avg_rating, 1)
            activity.review_count = len(reviews)
            db.commit()
