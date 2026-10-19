"""Météo et état de la mer en direct, avec repli explicite.

Les données ne constituent pas un avis de sécurité. L'utilisateur doit
respecter les drapeaux et consignes locales.
"""
from __future__ import annotations

import time
from datetime import datetime

import requests

CACHE_TTL = 1800
_cache: dict[str, tuple[float, dict]] = {}

WEATHER_LABELS = {
    0: "Ciel dégagé", 1: "Plutôt dégagé", 2: "Partiellement nuageux", 3: "Couvert",
    45: "Brouillard", 48: "Brouillard givrant", 51: "Bruine légère", 53: "Bruine",
    55: "Bruine dense", 61: "Pluie légère", 63: "Pluie", 65: "Pluie forte",
    71: "Neige", 80: "Averses", 81: "Averses modérées", 82: "Averses fortes",
    95: "Orage", 96: "Orage avec grêle", 99: "Orage violent",
}


def _get_json(url: str, params: dict) -> dict | None:
    try:
        response = requests.get(url, params=params, timeout=7)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        return None


def sea_state_from_wave(wave_height: float | None) -> str:
    if wave_height is None:
        return "État de la mer indisponible"
    if wave_height < 0.5:
        return "Mer calme"
    if wave_height < 1.0:
        return "Mer peu agitée"
    if wave_height < 1.5:
        return "Mer agitée"
    if wave_height < 2.5:
        return "Mer forte"
    return "Mer très forte"


def get_weather_sea(lat: float = 30.4278, lng: float = -9.5981) -> dict:
    key = f"{lat:.3f},{lng:.3f}"
    cached = _cache.get(key)
    if cached and time.time() - cached[0] < CACHE_TTL:
        return cached[1]

    forecast = _get_json("https://api.open-meteo.com/v1/forecast", {
        "latitude": lat, "longitude": lng,
        "current": "temperature_2m,wind_speed_10m,weather_code,relative_humidity_2m",
        "daily": "temperature_2m_max,temperature_2m_min,sunrise,sunset",
        "timezone": "Africa/Casablanca", "forecast_days": 3,
    })
    marine = _get_json("https://marine-api.open-meteo.com/v1/marine", {
        "latitude": lat, "longitude": lng,
        "current": "wave_height,wave_period,sea_surface_temperature",
        "timezone": "Africa/Casablanca", "forecast_days": 3,
    })

    result = {
        "available": False,
        "source": "Open-Meteo (prévision) + Open-Meteo Marine",
        "updated_at": datetime.now().strftime("%H:%M"),
        "temperature": None, "wind": None, "humidity": None,
        "weather_code": None, "summary": "Météo indisponible pour le moment",
        "wave_height": None, "wave_period": None, "sea_temp": None,
        "sea_state": "État de la mer indisponible", "sunrise": None, "sunset": None,
        "safety_note": "Donnée informative. Respectez les drapeaux et consignes locales.",
    }
    if forecast:
        current = forecast.get("current") or {}
        daily = forecast.get("daily") or {}
        code = current.get("weather_code")
        result.update({
            "available": True,
            "temperature": current.get("temperature_2m"),
            "wind": current.get("wind_speed_10m"),
            "humidity": current.get("relative_humidity_2m"),
            "weather_code": code,
            "summary": WEATHER_LABELS.get(code, "Conditions à confirmer"),
            "sunrise": (daily.get("sunrise") or [None])[0],
            "sunset": (daily.get("sunset") or [None])[0],
        })
    if marine:
        current = marine.get("current") or {}
        wave = current.get("wave_height")
        result.update({
            "wave_height": wave,
            "wave_period": current.get("wave_period"),
            "sea_temp": current.get("sea_surface_temperature"),
            "sea_state": sea_state_from_wave(wave),
        })
    if not forecast and not marine:
        result["summary"] = "Météo indisponible — connexion impossible"
    _cache[key] = (time.time(), result)
    return result
