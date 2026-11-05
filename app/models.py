
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.database import Base


# Enum para tipo de movimiento: entrada o salida
class MovementType(str, enum.Enum):
    IN = "in"
    OUT = "out"


class Product(Base):
    """
    Tabla 'products': almacena la información de cada producto.
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)          # Nombre del producto
    sku = Column(String(100), unique=True, nullable=False)  # Código único
    price = Column(Float, nullable=False)                # Precio
    stock = Column(Integer, default=0)                   # Cantidad en inventario
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relación: un producto tiene muchos movimientos de stock
    movements = relationship("StockMovement", back_populates="product", cascade="all, delete-orphan")


class StockMovement(Base):
    """
    Tabla 'stock_movements': registra cada entrada/salida de inventario.
    """
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    type = Column(Enum(MovementType), nullable=False)    # "in" o "out"
    quantity = Column(Integer, nullable=False)            # Cantidad movida
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relación inversa: cada movimiento pertenece a un producto
    product = relationship("Product", back_populates="movements")
    