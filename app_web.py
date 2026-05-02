"""Aplicación web para visitas de clientes con carga de archivos.

Permite adjuntar CSV/Excel con clientes, además de imágenes y otros archivos.
Muestra cliente más cercano y ruta sugerida con enlaces a Google Maps.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from io import BytesIO
from typing import List, Tuple

import pandas as pd
import streamlit as st


@dataclass(frozen=True)
class Cliente:
    nombre: str
    lat: float
    lon: float


def haversine_km(a: Cliente, b: Cliente) -> float:
    r = 6371.0
    lat1, lon1 = math.radians(a.lat), math.radians(a.lon)
    lat2, lon2 = math.radians(b.lat), math.radians(b.lon)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def cliente_mas_cercano(origen: Cliente, clientes: List[Cliente]) -> Tuple[Cliente, float]:
    elegido = min(clientes, key=lambda c: haversine_km(origen, c))
    return elegido, haversine_km(origen, elegido)


def ruta_vecino_mas_cercano(origen: Cliente, clientes: List[Cliente]) -> List[Cliente]:
    ruta: List[Cliente] = []
    actual = origen
    faltantes = clientes[:]
    while faltantes:
        siguiente, _ = cliente_mas_cercano(actual, faltantes)
        ruta.append(siguiente)
        faltantes.remove(siguiente)
        actual = siguiente
    return ruta


def url_maps(origen: Cliente, destino: Cliente) -> str:
    return (
        "https://www.google.com/maps/dir/?api=1"
        f"&origin={origen.lat},{origen.lon}"
        f"&destination={destino.lat},{destino.lon}"
        "&travelmode=driving"
    )


def url_maps_ruta(origen: Cliente, ruta: List[Cliente]) -> str:
    if not ruta:
        return ""
    destino = ruta[-1]
    waypoints = "|".join(f"{c.lat},{c.lon}" for c in ruta[:-1])
    url = (
        "https://www.google.com/maps/dir/?api=1"
        f"&origin={origen.lat},{origen.lon}"
        f"&destination={destino.lat},{destino.lon}"
        "&travelmode=driving"
    )
    if waypoints:
        url += f"&waypoints={waypoints}"
    return url


def cargar_clientes_desde_df(df: pd.DataFrame) -> List[Cliente]:
    required = {"nombre", "lat", "lon"}
    cols = {c.strip().lower() for c in df.columns}
    if not required.issubset(cols):
        raise ValueError("El archivo debe tener columnas: nombre, lat, lon")

    normalized = df.copy()
    normalized.columns = [c.strip().lower() for c in normalized.columns]
    return [
        Cliente(str(r["nombre"]).strip(), float(r["lat"]), float(r["lon"]))
        for _, r in normalized.iterrows()
    ]


st.set_page_config(page_title="Rutas de visitas", page_icon="📍", layout="wide")
st.title("📍 Optimización de rutas de visitas")
st.caption("Adjunta archivos y prioriza visitas por cercanía con enlaces a Google Maps.")

st.subheader("1) Adjuntar archivos")
archivos = st.file_uploader(
    "Sube uno o más archivos (Excel, CSV, JPG, PNG, PDF, TXT, etc.)",
    type=None,
    accept_multiple_files=True,
)

clientes: List[Cliente] = []

if archivos:
    for f in archivos:
        nombre = f.name.lower()
        st.write(f"- **{f.name}** ({f.type or 'tipo desconocido'})")

        if nombre.endswith(".csv"):
            df = pd.read_csv(f)
            st.dataframe(df.head(20), use_container_width=True)
            try:
                clientes = cargar_clientes_desde_df(df)
                st.success(f"Clientes cargados desde {f.name}: {len(clientes)}")
            except Exception as e:
                st.warning(f"{f.name}: {e}")

        elif nombre.endswith((".xlsx", ".xls")):
            df = pd.read_excel(BytesIO(f.getvalue()))
            st.dataframe(df.head(20), use_container_width=True)
            try:
                clientes = cargar_clientes_desde_df(df)
                st.success(f"Clientes cargados desde {f.name}: {len(clientes)}")
            except Exception as e:
                st.warning(f"{f.name}: {e}")

        elif nombre.endswith((".jpg", ".jpeg", ".png", ".webp")):
            st.image(f, caption=f.name, use_container_width=True)
        else:
            st.info(f"Archivo adjuntado: {f.name}")

st.subheader("2) Ubicación actual")
col1, col2 = st.columns(2)
with col1:
    lat_actual = st.number_input("Latitud", value=-12.05, format="%.6f")
with col2:
    lon_actual = st.number_input("Longitud", value=-77.04, format="%.6f")

if st.button("Calcular cliente más cercano y ruta", type="primary"):
    if not clientes:
        st.error("Primero sube un archivo CSV o Excel con columnas nombre, lat, lon.")
    else:
        origen = Cliente("Ubicación actual", lat_actual, lon_actual)
        cercano, distancia = cliente_mas_cercano(origen, clientes)
        ruta = ruta_vecino_mas_cercano(origen, clientes)

        st.subheader("🔔 Alerta de visita más cercana")
        st.success(f"Cliente más cercano: {cercano.nombre} ({distancia:.2f} km)")
        st.link_button("Abrir en Google Maps", url_maps(origen, cercano))

        st.subheader("Ruta sugerida")
        st.table(
            pd.DataFrame(
                [
                    {"orden": i + 1, "cliente": c.nombre, "lat": c.lat, "lon": c.lon}
                    for i, c in enumerate(ruta)
                ]
            )
        )
        st.link_button("Abrir ruta completa en Google Maps", url_maps_ruta(origen, ruta))


# --- Gestión de usuarios ---
st.divider()
st.header("👤 Manejo de usuarios")

if "usuarios" not in st.session_state:
    st.session_state.usuarios = [
        {"nombre": "Admin", "email": "admin@empresa.com", "rol": "Administrador", "activo": True},
        {"nombre": "Vendedor 1", "email": "vendedor1@empresa.com", "rol": "Vendedor", "activo": True},
    ]

with st.form("form_usuario", clear_on_submit=True):
    c1, c2 = st.columns(2)
    with c1:
        nombre_u = st.text_input("Nombre de usuario")
        email_u = st.text_input("Email")
    with c2:
        rol_u = st.selectbox("Rol", ["Administrador", "Supervisor", "Vendedor"])
        activo_u = st.checkbox("Activo", value=True)

    guardar = st.form_submit_button("Agregar usuario")

if guardar:
    if not nombre_u.strip() or not email_u.strip():
        st.error("Nombre y email son obligatorios.")
    elif any(u["email"].lower() == email_u.strip().lower() for u in st.session_state.usuarios):
        st.error("Ya existe un usuario con ese email.")
    else:
        st.session_state.usuarios.append(
            {
                "nombre": nombre_u.strip(),
                "email": email_u.strip().lower(),
                "rol": rol_u,
                "activo": activo_u,
            }
        )
        st.success("Usuario agregado correctamente.")

if st.session_state.usuarios:
    st.subheader("Listado de usuarios")
    usuarios_df = pd.DataFrame(st.session_state.usuarios)
    st.dataframe(usuarios_df, use_container_width=True)

    emails = [u["email"] for u in st.session_state.usuarios]
    email_sel = st.selectbox("Selecciona usuario para acciones", emails)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Desactivar / Activar usuario"):
            for u in st.session_state.usuarios:
                if u["email"] == email_sel:
                    u["activo"] = not u["activo"]
                    st.success(f"Estado actualizado para {u['nombre']}.")
                    break

    with col_b:
        if st.button("Eliminar usuario", type="secondary"):
            st.session_state.usuarios = [u for u in st.session_state.usuarios if u["email"] != email_sel]
            st.success("Usuario eliminado.")

