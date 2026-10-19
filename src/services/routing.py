"""Distances et estimations de temps de trajet.

Aucune donnée de trafic en temps réel : les durées sont explicitement des
estimations. Une intégration OSRM/Google pourra remplacer ce calcul.
"""
from __future__ import annotations

from math import asin, cos, radians, sin, sqrt


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return round(2 * r * asin(sqrt(a)), 2)


def travel_minutes(lat1: float, lon1: float, lat2: float, lon2: float, speed_kmh: float = 32.0) -> int:
    road_km = haversine_km(lat1, lon1, lat2, lon2) * 1.28
    return max(5, int(round((road_km / max(12.0, speed_kmh)) * 60)))


def distance_from_center(lat: float | None, lng: float | None, center=(30.4278, -9.5981)) -> float | None:
    if lat is None or lng is None:
        return None
    return haversine_km(center[0], center[1], lat, lng)


def map_points(items) -> list[dict]:
    points = []
    center = (30.4278, -9.5981)
    for item in items:
        if item.lat is None or item.lng is None:
            continue
        points.append({
            "id": item.id,
            "name": item.slug,
            "kind": item.kind,
            "lat": item.lat,
            "lng": item.lng,
            "distance_km": distance_from_center(item.lat, item.lng, center),
            "travel_minutes": travel_minutes(center[0], center[1], item.lat, item.lng),
        })
    return points
