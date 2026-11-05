
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.models import Product
from app.schemas import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """
    POST /products — Crea un nuevo producto.
    Si el SKU ya existe, devuelve error 400.
    """
    # Verificar que el SKU no esté duplicado
    existing = db.query(Product).filter(Product.sku == product.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")

    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.get("", response_model=List[ProductResponse])
def list_products(
    name: Optional[str] = Query(None, description="Filtrar por nombre"),
    db: Session = Depends(get_db)
):
    """
    GET /products — Lista todos los productos.
    Si se pasa ?name=algo, filtra por nombre (búsqueda parcial).
    """
    query = db.query(Product)
    if name:
        query = query.filter(Product.name.ilike(f"%{name}%"))
    return query.all()


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    GET /products/{id} — Consulta un producto por ID.
    Devuelve 404 si no existe.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db)
):
    """
    PUT /products/{id} — Actualiza un producto existente.
    Solo modifica los campos que se envíen.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Solo actualiza los campos que vienen en la petición
    update_data = product_data.model_dump(exclude_unset=True)

    # Si se intenta cambiar el SKU, verificar que no esté duplicado
    if "sku" in update_data:
        existing = db.query(Product).filter(
            Product.sku == update_data["sku"],
            Product.id != product_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="SKU already exists")

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """
    DELETE /products/{id} — Elimina un producto.
    Devuelve 404 si no existe.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return None
