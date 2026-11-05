
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# --- Esquemas de Producto ---

class ProductCreate(BaseModel):
    """Lo que el usuario envía para CREAR un producto."""
    name: str = Field(..., min_length=1, max_length=255)
    sku: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)       # Precio debe ser mayor a 0
    stock: int = Field(default=0, ge=0)   # Stock no puede ser negativo


class ProductUpdate(BaseModel):
    """Lo que el usuario envía para ACTUALIZAR un producto (todo opcional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)


class ProductResponse(BaseModel):
    """Lo que la API DEVUELVE cuando consultas un producto."""
    id: int
    name: str
    sku: str
    price: float
    stock: int
    created_at: datetime

    class Config:
        from_attributes = True  # Permite convertir objetos SQLAlchemy a Pydantic


# --- Esquemas de Movimiento de Stock ---

class StockMovementCreate(BaseModel):
    """Lo que el usuario envía para registrar un movimiento."""
    type: str = Field(..., pattern="^(in|out)$")  # Solo "in" o "out"
    quantity: int = Field(..., gt=0)               # Cantidad mayor a 0


class StockMovementResponse(BaseModel):
    """Lo que la API devuelve tras registrar un movimiento."""
    id: int
    product_id: int
    type: str
    quantity: int
    created_at: datetime

    class Config:
        from_attributes = True
