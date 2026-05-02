# what_sapp

App web para **visitas de clientes** que permite cargar archivos (Excel, CSV, JPG y otros), identificar el cliente más cercano y sugerir una ruta de visitas con enlaces directos a Google Maps.

## Funcionalidades

- Adjuntar múltiples archivos:
  - Datos: `.csv`, `.xlsx`, `.xls`
  - Imágenes: `.jpg`, `.jpeg`, `.png`, `.webp`
  - Otros: `.pdf`, `.txt`, etc. (se listan como adjuntos)
- Mostrar vista previa de los datos cargados.
- Calcular cliente más cercano desde ubicación actual (alerta).
- Proponer ruta de visitas por cercanía (heurística vecino más cercano).
- Abrir navegación del cliente más cercano y ruta completa en Google Maps.

## Ejecutar app web

```bash
pip install -r requirements.txt
streamlit run app_web.py
```

## Formato esperado para Excel/CSV

Debe contener columnas:

- `nombre`
- `lat`
- `lon`

Ejemplo:

```csv
nombre,lat,lon
Cliente A,-12.0464,-77.0428
Cliente B,-12.0060,-77.0560
```

## Dataset de ejemplo

Se mantiene `clientes_ejemplo.csv` para pruebas rápidas.

## Módulo de manejo de usuarios

La app incluye una sección para gestionar usuarios:

- Alta de usuario (nombre, email, rol, estado activo).
- Validación de email duplicado.
- Listado de usuarios en tabla.
- Activar/Desactivar usuario.
- Eliminar usuario.
