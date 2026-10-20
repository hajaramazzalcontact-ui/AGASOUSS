"""
Planificateur de séjour IA - Crée un programme jour par jour
"""

import json
from datetime import datetime, timedelta
from anthropic import Anthropic
import os

class TriplPlanner:
    """Planificateur de séjour personnalisé avec IA"""
    
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        
        self.client = Anthropic()
        self.model = "claude-3-5-sonnet-20241022"
    
    def create_itinerary(
        self,
        num_days: int,
        budget_mad: float,
        group_composition: dict,
        interests: list,
        language: str = "fr",
        weather_data: dict = None
    ) -> dict:
        """
        Crée un itinéraire jour par jour
        
        Args:
            num_days: Nombre de jours du séjour
            budget_mad: Budget total en MAD
            group_composition: {"adults": 2, "children": [5, 8]}
            interests: ["Aventure", "Culture", "Mer", ...]
            language: fr, en, ar, es
            weather_data: Prévisions météo
        
        Returns:
            Dict avec programme jour par jour
        """
        
        prompt = self._build_prompt(
            num_days, budget_mad, group_composition, interests, language, weather_data
        )
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            response_text = response.content[0].text
            
            # Parser la réponse JSON
            itinerary = self._parse_itinerary(response_text)
            return itinerary
            
        except Exception as e:
            return {"error": str(e)}
    
    def _build_prompt(self, num_days, budget_mad, group, interests, language, weather):
        """Construit le prompt pour Claude"""
        
        group_desc = f"{group.get('adults', 1)} adulte(s)"
        if group.get('children'):
            ages = ', '.join(str(a) for a in group['children'])
            group_desc += f", enfants ({ages} ans)"
        
        weather_info = ""
        if weather:
            weather_info = f"\nMétéo prévue: {json.dumps(weather)}"
        
        interests_str = ", ".join(interests) if interests else "divers"
        
        lang_names = {
            "fr": "Français",
            "en": "English",
            "ar": "العربية",
            "es": "Español"
        }
        
        prompt = f"""
Tu es un expert en tourisme à Agadir et Taghazout. Crée un itinéraire détaillé.

DEMANDE CLIENT:
- Durée: {num_days} jours
- Groupe: {group_desc}
- Budget total: {budget_mad} MAD
- Intérêts: {interests_str}
{weather_info}

ACTIVITÉS DISPONIBLES:
- Sortie Dauphins (350 MAD, ⭐4.8)
- Médina d'Agadir (200 MAD, ⭐4.6)
- Quad Safari (400 MAD, ⭐4.7)
- Ateliers artisanaux (180 MAD, ⭐4.9)
- Crocoparc (120 MAD, ⭐4.3)
- Golf 18 trous (500 MAD, ⭐4.4)

RESTAURANTS:
- Pêcheurs (fruits de mer, €€€)
- Riad Palais Des Roses (marocain, €€€)
- Café Marocain (€)

Crée un programme jour par jour au format JSON avec:
- jour (numéro)
- titre
- activités (avec horaires)
- restaurants (petit-déj, déj, dîner)
- transport
- budget_jour
- notes (plans B météo, conseils)

Réponds UNIQUEMENT en JSON valide, pas d'explication.
Langue réponse: {lang_names.get(language, 'Français')}
"""
        
        return prompt
    
    def _parse_itinerary(self, response_text: str) -> dict:
        """Parse la réponse JSON de Claude"""
        
        try:
            # Chercher JSON dans la réponse
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start == -1 or end == 0:
                return {"error": "Pas de JSON trouvé dans la réponse"}
            
            json_str = response_text[start:end]
            itinerary = json.loads(json_str)
            return itinerary
            
        except json.JSONDecodeError as e:
            return {"error": f"JSON parsing error: {str(e)}"}
