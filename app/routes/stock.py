
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, StockMovement
from app.schemas import StockMovementCreate, StockMovementResponse

router = APIRouter(tags=["Stock"])


@router.post(
    "/products/{product_id}/stock",
    response_model=StockMovementResponse,
    status_code=201
)
def create_stock_movement(
    product_id: int,
    movement: StockMovementCreate,
    db: Session = Depends(get_db)
):
    """
    POST /products/{id}/stock — Registra un movimiento de inventario.

    - type "in"  → suma quantity al stock del producto
    - type "out" → resta quantity al stock (error 400 si no hay suficiente)
    """
    # Buscar el producto
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Validar stock suficiente para salidas
    if movement.type == "out" and product.stock < movement.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock. Available: {product.stock}, requested: {movement.quantity}"
        )

    # Actualizar el stock del producto
    if movement.type == "in":
        product.stock += movement.quantity
    else:
        product.stock -= movement.quantity

    # Crear el registro del movimiento
    db_movement = StockMovement(
        product_id=product_id,
        type=movement.type,
        quantity=movement.quantity
    )
    db.add(db_movement)
    db.commit()
    db.refresh(db_movement)
    return db_movement
