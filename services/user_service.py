"""
Service pour les utilisateurs et l'authentification
"""

import uuid
import bcrypt
from sqlalchemy.orm import Session
from data.models import User, AdminUser
from typing import Optional
from datetime import datetime

class UserService:
    """Gestion des utilisateurs"""
    
    @staticmethod
    def create_user(db: Session, user_data: dict) -> User:
        """Crée un nouveau client"""
        user = User(
            id=str(uuid.uuid4()),
            **user_data
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def get_user(db: Session, user_id: str) -> Optional[User]:
        """Récupère un utilisateur par ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Récupère un utilisateur par email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_phone(db: Session, phone: str) -> Optional[User]:
        """Récupère un utilisateur par téléphone"""
        return db.query(User).filter(User.phone == phone).first()
    
    @staticmethod
    def update_user(db: Session, user_id: str, user_data: dict) -> Optional[User]:
        """Met à jour un utilisateur"""
        user = UserService.get_user(db, user_id)
        if not user:
            return None
        
        for key, value in user_data.items():
            setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def delete_user(db: Session, user_id: str) -> bool:
        """Supprime un utilisateur"""
        user = UserService.get_user(db, user_id)
        if not user:
            return False
        
        db.delete(user)
        db.commit()
        return True

class AdminUserService:
    """Gestion des administrateurs et authentification"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash un mot de passe avec bcrypt"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Vérifie un mot de passe"""
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    
    @staticmethod
    def create_admin(db: Session, admin_data: dict) -> AdminUser:
        """Crée un nouvel administrateur"""
        admin_data["password_hash"] = AdminUserService.hash_password(admin_data.pop("password"))
        
        admin = AdminUser(
            id=str(uuid.uuid4()),
            **admin_data
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin
    
    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> Optional[AdminUser]:
        """Authentifie un administrateur"""
        admin = db.query(AdminUser).filter(AdminUser.email == email).first()
        
        if not admin or not admin.is_active:
            return None
        
        if AdminUserService.verify_password(password, admin.password_hash):
            admin.last_login = datetime.utcnow()
            db.commit()
            return admin
        
        return None
    
    @staticmethod
    def get_admin(db: Session, admin_id: str) -> Optional[AdminUser]:
        """Récupère un administrateur par ID"""
        return db.query(AdminUser).filter(AdminUser.id == admin_id).first()
    
    @staticmethod
    def get_admin_by_email(db: Session, email: str) -> Optional[AdminUser]:
        """Récupère un administrateur par email"""
        return db.query(AdminUser).filter(AdminUser.email == email).first()
    
    @staticmethod
    def update_admin(db: Session, admin_id: str, admin_data: dict) -> Optional[AdminUser]:
        """Met à jour un administrateur"""
        admin = AdminUserService.get_admin(db, admin_id)
        if not admin:
            return None
        
        # Ne pas mettre à jour le password via cette méthode
        if "password" in admin_data:
            admin_data.pop("password")
        
        for key, value in admin_data.items():
            setattr(admin, key, value)
        
        admin.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(admin)
        return admin
