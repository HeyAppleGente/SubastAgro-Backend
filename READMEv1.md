# SubastAgro Backend - Arquitectura Base (READMEv1)
**Proyecto:** Plataforma de Subastas de Ganado Vacuno (`subastagro_db`)  
**Dirigido a:** Prof. LUIS GUILLERMO MORELO  

## 1. Arquitectura Modular por Dominios
- `app/auth/`: Autenticación JWT (Access + Refresh) y Cookies `HttpOnly`.
- `app/users/`: Gestión de usuarios, roles (`ADMINISTRADOR`, `GANADERO`, `COMPRADOR`) y tabla asociativa `usuario_roles`.
- `app/cattle_lots/`: Catálogo de razas (`razas_ganado`) y lotes vacunos (`lotes_ganado`).
- `app/auctions/`: Eventos de subasta (`eventos_subasta`).
- `app/bids/`: Pujas y ofertas (`pujas_ofertas`).
- `app/adjudications/`: Actas de adjudicación (`actas_adjudicacion`).
- `app/core/`: Configuración `.env`, SQLAlchemy 2.0, seguridad Bcrypt/JWT y middlewares OWASP.

## 2. Modelo ER (8 Tablas en 3FN - PostgreSQL 18)
1. `usuarios` ↔ `roles` (N:M vía `usuario_roles`)
2. `usuarios` (Ganadero) ↔ `lotes_ganado` (1:N)
3. `razas_ganado` ↔ `lotes_ganado` (1:N)
4. `lotes_ganado` ↔ `eventos_subasta` (1:1)
5. `eventos_subasta` ↔ `pujas_ofertas` (1:N)
6. `usuarios` (Comprador) ↔ `pujas_ofertas` (1:N)
7. `eventos_subasta` ↔ `actas_adjudicacion` (1:1)

## 3. Instalación Local
```bash
python -m venv venv
# Windows PowerShell: .\venv\Scripts\Activate.ps1
# Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload
```
Documentación interactiva disponible en `http://localhost:8000/docs`.
