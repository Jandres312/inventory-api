
from fastapi import FastAPI
from app.database import engine, Base
from app.routes import products, stock

# Crear todas las tablas en la base de datos al iniciar
Base.metadata.create_all(bind=engine)

# Crear la aplicación FastAPI
app = FastAPI(
    title="Inventory Management API",
    description="API REST para gestión de inventario - Prueba Técnica N1",
    version="1.0.0"
)


@app.get("/health")
def health_check():
    """GET /health — Verifica que la API está funcionando."""
    return {"status": "ok"}


# Registrar las rutas
app.include_router(products.router)
app.include_router(stock.router)
