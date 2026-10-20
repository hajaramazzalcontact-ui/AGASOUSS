"""
Service pour les réservations et le panier
"""

import uuid
import random
import string
from datetime import datetime
from sqlalchemy.orm import Session
from data.models import Booking, BookingItem, User
from typing import List, Optional, Dict

class BookingService:
    """Gestion des réservations et du panier"""
    
    @staticmethod
    def create_booking(db: Session, user_id: str, booking_data: dict) -> Booking:
        """Crée une nouvelle réservation"""
        booking = Booking(
            id=str(uuid.uuid4()),
            user_id=user_id,
            confirmation_code=BookingService.generate_confirmation_code(),
            **booking_data
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)
        return booking
    
    @staticmethod
    def get_booking(db: Session, booking_id: str) -> Optional[Booking]:
        """Récupère une réservation par son ID"""
        return db.query(Booking).filter(Booking.id == booking_id).first()
    
    @staticmethod
    def get_user_bookings(db: Session, user_id: str) -> List[Booking]:
        """Récupère toutes les réservations d'un utilisateur"""
        return db.query(Booking).filter(Booking.user_id == user_id).order_by(
            Booking.created_at.desc()
        ).all()
    
    @staticmethod
    def update_booking_status(db: Session, booking_id: str, status: str) -> Optional[Booking]:
        """Met à jour le statut d'une réservation"""
        booking = BookingService.get_booking(db, booking_id)
        if not booking:
            return None
        
        booking.status = status
        booking.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(booking)
        return booking
    
    @staticmethod
    def calculate_ai_score(booking: Booking) -> int:
        """
        Calcule un score de réservation (0-100) pour prioriser les confirmations
        Basé sur : montant, délai, taille du groupe, historique du client
        """
        score = 50  # Score de base
        
        # Bonus pour montant élevé (+20 max)
        if booking.total_price_mad and booking.total_price_mad > 1000:
            score += 20
        elif booking.total_price_mad and booking.total_price_mad > 500:
            score += 15
        elif booking.total_price_mad and booking.total_price_mad > 200:
            score += 10
        
        # Bonus pour groupe important (+15 max)
        if booking.participant_count and booking.participant_count > 5:
            score += 15
        elif booking.participant_count and booking.participant_count > 2:
            score += 10
        
        # Malus pour réservation urgente (dans 24h) (-10)
        if booking.activity_date:
            days_until = (booking.activity_date - datetime.now().date()).days
            if days_until < 1:
                score -= 10
        
        # Bonus pour acompte versé (+20)
        if booking.deposit_paid_mad and booking.deposit_paid_mad > 0:
            score += 20
        
        return min(100, max(0, score))
    
    @staticmethod
    def generate_confirmation_code() -> str:
        """Génère un code de confirmation unique"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    @staticmethod
    def add_item_to_cart(
        db: Session,
        booking_id: str,
        item_type: str,
        item_id: str,
        quantity: int = 1,
        price: float = 0
    ) -> Booking:
        """Ajoute un article au panier"""
        booking = BookingService.get_booking(db, booking_id)
        if not booking:
            return None
        
        # Initialiser booking_items si vide
        if not booking.booking_items:
            booking.booking_items = []
        
        # Ajouter l'article
        new_item = {
            "item_type": item_type,
            "item_id": item_id,
            "quantity": quantity,
            "price": price,
            "added_at": datetime.utcnow().isoformat()
        }
        
        booking.booking_items.append(new_item)
        BookingService._recalculate_total(booking)
        
        db.commit()
        db.refresh(booking)
        return booking
    
    @staticmethod
    def remove_item_from_cart(db: Session, booking_id: str, item_id: str) -> Booking:
        """Supprime un article du panier"""
        booking = BookingService.get_booking(db, booking_id)
        if not booking or not booking.booking_items:
            return booking
        
        booking.booking_items = [
            item for item in booking.booking_items
            if item.get("item_id") != item_id
        ]
        
        BookingService._recalculate_total(booking)
        db.commit()
        db.refresh(booking)
        return booking
    
    @staticmethod
    def _recalculate_total(booking: Booking):
        """Recalcule le total du panier"""
        if not booking.booking_items:
            booking.total_price_mad = 0
            return
        
        total = sum(
            item.get("price", 0) * item.get("quantity", 1)
            for item in booking.booking_items
        )
        booking.total_price_mad = total
    
    @staticmethod
    def get_pending_confirmations(db: Session, days_limit: int = 1) -> List[Booking]:
        """Récupère les réservations en attente de confirmation avec score élevé"""
        bookings = db.query(Booking).filter(
            Booking.status == "pending"
        ).all()
        
        # Scorer et trier
        scored = [
            (booking, BookingService.calculate_ai_score(booking))
            for booking in bookings
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return [b[0] for b in scored]
    
    @staticmethod
    def record_deposit(db: Session, booking_id: str, amount: float) -> Optional[Booking]:
        """Enregistre un acompte versé"""
        booking = BookingService.get_booking(db, booking_id)
        if not booking:
            return None
        
        booking.deposit_paid_mad = (booking.deposit_paid_mad or 0) + amount
        
        # Si dépôt = montant total, confirmer
        if booking.deposit_paid_mad >= booking.total_price_mad:
            booking.status = "deposit_received"
        
        db.commit()
        db.refresh(booking)
        return booking
