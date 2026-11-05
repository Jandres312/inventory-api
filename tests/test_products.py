
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app


# ============================================================
# CONFIGURACIÓN DE TESTS (fixtures)
# ============================================================

# Usamos SQLite en memoria para los tests (no necesita PostgreSQL)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


@pytest.fixture(autouse=True)
def setup_database():
    """Crea las tablas antes de cada test y las borra después."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Crea una sesión de base de datos para los tests."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """Cliente de prueba que usa la DB de testing."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ============================================================
# Datos de prueba reutilizables
# ============================================================

def sample_product():
    """Devuelve un producto válido para usar en los tests."""
    return {
        "name": "Laptop HP",
        "sku": "LAP-001",
        "price": 999.99,
        "stock": 50
    }


# ============================================================
# TEST 1: Health check
# ============================================================

def test_health_check(client):
    """Prueba que GET /health devuelve {"status": "ok"}."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ============================================================
# TEST 2: Crear un producto válido
# ============================================================

def test_create_product_valid(client):
    """Prueba que POST /products crea un producto correctamente."""
    response = client.post("/products", json=sample_product())
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Laptop HP"
    assert data["sku"] == "LAP-001"
    assert data["price"] == 999.99
    assert data["stock"] == 50
    assert "id" in data
    assert "created_at" in data


# ============================================================
# TEST 3: SKU duplicado
# ============================================================

def test_create_product_duplicate_sku(client):
    """Prueba que no se puede crear dos productos con el mismo SKU."""
    client.post("/products", json=sample_product())
    response = client.post("/products", json=sample_product())
    assert response.status_code == 400
    assert "SKU already exists" in response.json()["detail"]


# ============================================================
# TEST 4: Validaciones de precio y stock (PARAMETRIZADA)
# ============================================================

@pytest.mark.parametrize("invalid_data, description", [
    ({"name": "Test", "sku": "T-001", "price": -10, "stock": 5},
     "precio negativo"),
    ({"name": "Test", "sku": "T-002", "price": 0, "stock": 5},
     "precio cero"),
    ({"name": "Test", "sku": "T-003", "price": 10, "stock": -1},
     "stock negativo"),
    ({"name": "", "sku": "T-004", "price": 10, "stock": 5},
     "nombre vacio"),
])
def test_create_product_invalid_data(client, invalid_data, description):
    """Prueba PARAMETRIZADA: datos invalidos son rechazados."""
    response = client.post("/products", json=invalid_data)
    assert response.status_code == 422, (
        f"Deberia fallar con: {description}"
    )


# ============================================================
# TEST 5: Producto no encontrado (404)
# ============================================================

def test_get_product_not_found(client):
    """Prueba que buscar un producto que no existe devuelve 404."""
    response = client.get("/products/9999")
    assert response.status_code == 404
    assert "Product not found" in response.json()["detail"]


# ============================================================
# TEST 6: Listar productos
# ============================================================

def test_list_products(client):
    """Prueba que GET /products devuelve la lista de productos."""
    client.post("/products", json=sample_product())
    response = client.get("/products")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["sku"] == "LAP-001"


# ============================================================
# TEST 7: Movimiento de stock IN (entrada)
# ============================================================

def test_stock_movement_in(client):
    """Prueba que un movimiento 'in' suma al stock."""
    create_resp = client.post("/products", json=sample_product())
    product_id = create_resp.json()["id"]

    response = client.post(
        f"/products/{product_id}/stock",
        json={"type": "in", "quantity": 20}
    )
    assert response.status_code == 201

    product = client.get(f"/products/{product_id}").json()
    assert product["stock"] == 70


# ============================================================
# TEST 8: Movimiento de stock OUT válido (salida)
# ============================================================

def test_stock_movement_out_valid(client):
    """Prueba que un movimiento 'out' resta del stock."""
    create_resp = client.post("/products", json=sample_product())
    product_id = create_resp.json()["id"]

    response = client.post(
        f"/products/{product_id}/stock",
        json={"type": "out", "quantity": 10}
    )
    assert response.status_code == 201

    product = client.get(f"/products/{product_id}").json()
    assert product["stock"] == 40


# ============================================================
# TEST 9: Movimiento OUT que excede el stock (error)
# ============================================================

def test_stock_movement_out_exceeds_stock(client):
    """Prueba que no se puede sacar mas stock del que hay."""
    create_resp = client.post("/products", json=sample_product())
    product_id = create_resp.json()["id"]

    response = client.post(
        f"/products/{product_id}/stock",
        json={"type": "out", "quantity": 100}
    )
    assert response.status_code == 400
    assert "Insufficient stock" in response.json()["detail"]


# ============================================================
# TEST 10: Eliminar producto
# ============================================================

def test_delete_product(client):
    """Prueba que DELETE /products/{id} elimina el producto."""
    create_resp = client.post("/products", json=sample_product())
    product_id = create_resp.json()["id"]

    response = client.delete(f"/products/{product_id}")
    assert response.status_code == 204

    response = client.get(f"/products/{product_id}")
    assert response.status_code == 404