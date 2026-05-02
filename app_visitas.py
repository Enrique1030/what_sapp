"""App simple para optimizar visitas de clientes por cercanía.

- Carga clientes desde CSV (nombre,lat,lon).
- Calcula cliente más cercano al punto actual.
- Genera una ruta heurística (vecino más cercano).
- Muestra enlaces de Google Maps para navegación.
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple


@dataclass(frozen=True)
class Cliente:
    nombre: str
    lat: float
    lon: float


def haversine_km(a: Cliente, b: Cliente) -> float:
    """Distancia en km entre dos puntos geográficos."""
    r = 6371.0
    lat1, lon1 = math.radians(a.lat), math.radians(a.lon)
    lat2, lon2 = math.radians(b.lat), math.radians(b.lon)
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def cargar_clientes(csv_path: Path) -> List[Cliente]:
    clientes: List[Cliente] = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            clientes.append(
                Cliente(
                    nombre=row["nombre"].strip(),
                    lat=float(row["lat"]),
                    lon=float(row["lon"]),
                )
            )
    if not clientes:
        raise ValueError("No hay clientes en el archivo CSV.")
    return clientes


def cliente_mas_cercano(origen: Cliente, clientes: Iterable[Cliente]) -> Tuple[Cliente, float]:
    elegido = min(clientes, key=lambda c: haversine_km(origen, c))
    return elegido, haversine_km(origen, elegido)


def ruta_vecino_mas_cercano(origen: Cliente, pendientes: List[Cliente]) -> List[Cliente]:
    ruta: List[Cliente] = []
    actual = origen
    faltantes = pendientes[:]

    while faltantes:
        siguiente, _ = cliente_mas_cercano(actual, faltantes)
        ruta.append(siguiente)
        faltantes.remove(siguiente)
        actual = siguiente

    return ruta


def url_google_maps_direccion(origen: Cliente, destino: Cliente) -> str:
    return (
        "https://www.google.com/maps/dir/?api=1"
        f"&origin={origen.lat},{origen.lon}"
        f"&destination={destino.lat},{destino.lon}"
        "&travelmode=driving"
    )


def url_google_maps_ruta(origen: Cliente, ruta: List[Cliente]) -> str:
    if not ruta:
        return ""
    destino = ruta[-1]
    waypoints = "|".join(f"{c.lat},{c.lon}" for c in ruta[:-1])
    base = (
        "https://www.google.com/maps/dir/?api=1"
        f"&origin={origen.lat},{origen.lon}"
        f"&destination={destino.lat},{destino.lon}"
        "&travelmode=driving"
    )
    if waypoints:
        base += f"&waypoints={waypoints}"
    return base


def main() -> None:
    parser = argparse.ArgumentParser(description="Optimización simple de visitas de clientes")
    parser.add_argument("--csv", type=Path, required=True, help="Archivo CSV con columnas nombre,lat,lon")
    parser.add_argument("--lat", type=float, required=True, help="Latitud de la ubicación actual")
    parser.add_argument("--lon", type=float, required=True, help="Longitud de la ubicación actual")
    args = parser.parse_args()

    clientes = cargar_clientes(args.csv)
    origen = Cliente(nombre="Ubicación actual", lat=args.lat, lon=args.lon)

    cercano, dist = cliente_mas_cercano(origen, clientes)
    ruta = ruta_vecino_mas_cercano(origen, clientes)

    print("🔔 ALERTA: cliente más cercano")
    print(f"- {cercano.nombre} ({dist:.2f} km)")
    print(f"- Ir ahora: {url_google_maps_direccion(origen, cercano)}")
    print("\nRuta sugerida de visitas:")
    for i, c in enumerate(ruta, start=1):
        print(f"{i}. {c.nombre} ({c.lat}, {c.lon})")

    print("\nAbrir toda la ruta en Google Maps:")
    print(url_google_maps_ruta(origen, ruta))


if __name__ == "__main__":
    main()
