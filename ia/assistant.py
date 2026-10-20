"""
Assistant conversationnel multilingue IA (Claude)
"""

import os
from anthropic import Anthropic
from sqlalchemy.orm import Session
from data.database import SessionLocal
from data.models import Activity, Restaurant, Accommodation

class AIAssistant:
    """Assistant IA multilingue basé sur Claude"""
    
    def __init__(self):
        """Initialise le client Anthropic"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("⚠️ ANTHROPIC_API_KEY non configurée. Ajoute-la dans .env")
        
        self.client = Anthropic()
        self.model = "claude-3-5-sonnet-20241022"
        self.conversations = {}  # Stocker les conversations par session
    
    def get_catalog_context(self, db: Session) -> str:
        """Construit le contexte du catalogue pour le prompt"""
        
        # Récupérer les activités
        activities = db.query(Activity).filter(Activity.is_active == True).limit(100).all()
        activities_text = "\n".join([
            f"- {a.name_fr}: {a.description_short_fr} ({a.price_mad} MAD, ⭐{a.avg_rating}/5)"
            for a in activities
        ])
        
        # Récupérer les restaurants
        restaurants = db.query(Restaurant).filter(Restaurant.is_active == True).limit(50).all()
        restaurants_text = "\n".join([
            f"- {r.name}: {', '.join(r.cuisine_types or [])} ({r.price_range})"
            for r in restaurants
        ])
        
        # Récupérer les hébergements
        accommodations = db.query(Accommodation).filter(Accommodation.is_active == True).limit(50).all()
        accommodations_text = "\n".join([
            f"- {a.name} ({a.zone}): {a.type}"
            for a in accommodations
        ])
        
        context = f"""
Tu es un assistant touristique expert pour AZUL AGADIR, une plateforme de tourisme à Agadir et Taghazout au Maroc.

CATALOGUE DISPONIBLE:

**Activités:**
{activities_text}

**Restaurants:**
{restaurants_text}

**Hébergements:**
{accommodations_text}

RÈGLES:
1. Réponds UNIQUEMENT sur la base du catalogue fourni
2. Si l'information n'est pas dans le catalogue, dis: "Je n'ai pas cette information. Contacte notre support."
3. Sois amical, chaleureux et recommande les meilleures options
4. Propose des packages complets (activité + restaurant + hôtel)
5. Reste concis et utile
6. Utilise la langue du client (français, anglais, arabe, espagnol)
"""
        
        return context
    
    def chat(self, session_id: str, user_message: str, language: str = "fr") -> str:
        """
        Conversation multilingue avec l'IA
        Retourne la réponse de l'IA
        """
        
        db = SessionLocal()
        catalog_context = self.get_catalog_context(db)
        db.close()
        
        # Initialiser la conversation si nouvelle
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        # Ajouter le message utilisateur
        self.conversations[session_id].append({
            "role": "user",
            "content": user_message
        })
        
        # Construire le système prompt avec le catalogue
        system_prompt = catalog_context
        
        # Langue du client
        language_names = {
            "fr": "Français",
            "en": "English",
            "ar": "العربية",
            "es": "Español"
        }
        system_prompt += f"\nRéponds en {language_names.get(language, 'Français')}."
        
        try:
            # Appel à l'API Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                system=system_prompt,
                messages=self.conversations[session_id]
            )
            
            # Extraire la réponse
            assistant_message = response.content[0].text
            
            # Ajouter à l'historique
            self.conversations[session_id].append({
                "role": "assistant",
                "content": assistant_message
            })
            
            return assistant_message
            
        except Exception as e:
            error_message = f"❌ Erreur IA : {str(e)}"
            print(error_message)
            return error_message
    
    def clear_conversation(self, session_id: str):
        """Efface l'historique d'une conversation"""
        if session_id in self.conversations:
            del self.conversations[session_id]
