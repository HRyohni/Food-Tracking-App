"""Seed the shared database with demo data for a live presentation.

Run it inside any running backend container — they all ship Python, the deps and
the Ashared package, and they already point at the shared database:

    docker compose cp seed.py customer:/app/seed.py
    docker compose exec customer python /app/seed.py

By default the seven demo tables are WIPED and rebuilt from scratch, so the
script is safely re-runnable between demo runs (ids restart at 1). Pass --keep
to append on top of whatever is already there instead.

Every seeded account uses the password "demo123", except the demo account that
exists on all three services: test@test.com / test.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import Boolean, Column, DateTime, Integer, String, text

from Ashared.database import Base, SessionLocal, engine
from Ashared.domain import CourierPing, Order, OrderItem, OrderStatus, Product
from Ashared.security import hash_password


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# The three account tables are each owned by their own service. Importing those
# modules here is impossible in one process (all three are named `models` and
# import a `database` of their own), so mirror the three declarations against
# the same shared Base. Keep these in sync with the services' models.py.
# ---------------------------------------------------------------------------
class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


class Partner(Base):
    __tablename__ = "partners"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    contact_email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


class Worker(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    specialty = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


TABLES = ("order_items", "courier_pings", "orders", "products",
          "customers", "partners", "workers")

DEMO_PASSWORD = "demo123"
# The demo account present on all three services. The address has to be a real
# one: the *Out schemas type `email` as EmailStr, and Pydantic validates that on
# the way OUT too — a bare "test" makes /me and the whole /customers/ listing
# fail with a 500 ResponseValidationError.
TEST_LOGIN = "test@test.com"
TEST_PASSWORD = "test"

NOW = _utcnow()

# bcrypt costs ~0.3s a hash; the demo only needs two distinct ones.
_pw_cache: dict[str, str] = {}


def pw(raw: str) -> str:
    if raw not in _pw_cache:
        _pw_cache[raw] = hash_password(raw)
    return _pw_cache[raw]


def ago(days: int = 0, hours: int = 0, minutes: int = 0) -> datetime:
    return NOW - timedelta(days=days, hours=hours, minutes=minutes)


# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------
PARTNERS = [
    {
        "company_name": "Pizzeria Napoli",
        "contact_email": "napoli@demo.hr",
        "phone": "+385 1 4811 222",
        "menu": [
            ("Margherita", "Rajcica, mozzarella, bosiljak", "8.50", True),
            ("Capricciosa", "Sunka, sampinjoni, masline", "10.50", True),
            ("Quattro Formaggi", "Cetiri vrste sira", "11.00", True),
            ("Vegetariana", "Sezonsko povrce, mozzarella", "9.50", True),
            ("Calzone", "Punjena pizza sa sunkom i sirom", "10.00", False),
            ("Tiramisu", "Domaci desert", "4.50", True),
        ],
    },
    {
        "company_name": "Sushi Zen",
        "contact_email": "zen@demo.hr",
        "phone": "+385 1 3355 108",
        "menu": [
            ("Sake Nigiri (6 kom)", "Losos na rizi", "6.00", True),
            ("California Maki (8 kom)", "Surimi, avokado, krastavac", "9.50", True),
            ("Sashimi Mix", "Losos, tuna, orada", "14.00", True),
            ("Ramen Tonkotsu", "Juha od svinjskih kostiju, jaje", "11.50", True),
            ("Gyoza (5 kom)", "Przene okruglice s piletinom", "7.00", True),
            ("Miso juha", "Tofu, wakame, mladi luk", "3.50", True),
        ],
    },
    {
        "company_name": "Burger Bar Zagreb",
        "contact_email": "burgerbar@demo.hr",
        "phone": "+385 1 6100 477",
        "menu": [
            ("Classic Burger", "180g junetine, salata, rajcica", "9.00", True),
            ("Cheeseburger", "Cheddar, kiseli krastavci", "9.90", True),
            ("BBQ Bacon Burger", "Slanina, BBQ umak, hrskavi luk", "11.50", True),
            ("Veggie Burger", "Pljeskavica od slanutka", "9.00", True),
            ("Pomfrit", "Velika porcija", "3.50", True),
            ("Onion Rings", "Kolutici luka u tijestu", "4.00", True),
        ],
    },
    {
        "company_name": "Green Garden",
        "contact_email": "green@demo.hr",
        "phone": "+385 1 2299 640",
        "menu": [
            ("Caesar salata", "Piletina, parmezan, krutoni", "8.50", True),
            ("Quinoa Bowl", "Quinoa, avokado, slanutak", "10.00", True),
            ("Falafel Wrap", "Falafel, humus, salata", "8.00", True),
            ("Zeleni smoothie", "Spinat, banana, jabuka", "5.50", True),
            ("Humus s pitom", "Domaci humus", "6.00", True),
        ],
    },
    {
        "company_name": "Slasticarna Dolce",
        "contact_email": "dolce@demo.hr",
        "phone": "+385 1 4813 900",
        "menu": [
            ("New York Cheesecake", "Uz umak od sumskog voca", "4.80", True),
            ("Palacinke (3 kom)", "Nutella ili marmelada", "5.50", True),
            ("Sladoled (kugla)", "Vanilija, cokolada, jagoda", "2.00", True),
            ("Baklava", "Orasi i med", "4.00", False),
            ("Espresso", "Dvostruki", "2.20", True),
        ],
    },
    {
        "company_name": "Test Restoran",
        "contact_email": TEST_LOGIN,
        "phone": "+385 1 0000 000",
        "password": TEST_PASSWORD,
        "menu": [
            ("Test Pizza", "Demo artikl za prezentaciju", "10.00", True),
            ("Test Burger", "Demo artikl za prezentaciju", "9.00", True),
            ("Test Salata", "Demo artikl za prezentaciju", "7.00", True),
            ("Test Sok", "Demo artikl za prezentaciju", "3.00", True),
        ],
    },
]

CUSTOMERS = [
    {"name": "Test Korisnik", "email": TEST_LOGIN, "phone": "+385 91 000 0000",
     "password": TEST_PASSWORD},
    {"name": "Ana Horvat", "email": "ana@demo.hr", "phone": "+385 91 234 5678"},
    {"name": "Ivan Kovacevic", "email": "ivan@demo.hr", "phone": "+385 98 111 2233"},
    {"name": "Marija Novak", "email": "marija@demo.hr", "phone": "+385 95 876 5432"},
    {"name": "Luka Babic", "email": "luka@demo.hr", "phone": "+385 99 345 6789"},
    {"name": "Petra Juric", "email": "petra@demo.hr", "phone": "+385 91 555 4433"},
    {"name": "Marko Radic", "email": "marko@demo.hr", "phone": "+385 92 777 8899",
     "is_active": False},
]

WORKERS = [
    {"name": "Test Dostavljac", "email": TEST_LOGIN, "phone": "+385 91 000 0001",
     "specialty": "Automobil", "password": TEST_PASSWORD},
    {"name": "Josip Peric", "email": "josip@demo.hr", "phone": "+385 91 222 3344",
     "specialty": "Bicikl"},
    {"name": "Nikola Tomic", "email": "nikola@demo.hr", "phone": "+385 98 444 5566",
     "specialty": "Skuter"},
    {"name": "Ines Matic", "email": "ines@demo.hr", "phone": "+385 95 666 7788",
     "specialty": "Automobil"},
]

# (customer, partner, [(artikl, kolicina)], status, courier, adresa, created_at)
ORDERS = [
    # ---- Live queue: partner just got these, nothing done yet -------------
    (TEST_LOGIN, TEST_LOGIN, [("Test Pizza", 1), ("Test Sok", 2)],
     OrderStatus.PENDING, None, "Ilica 242, Zagreb", ago(minutes=4)),
    ("ana@demo.hr", "napoli@demo.hr", [("Margherita", 2), ("Tiramisu", 1)],
     OrderStatus.PENDING, None, "Vukovarska 15, Zagreb", ago(minutes=9)),
    ("ivan@demo.hr", "burgerbar@demo.hr", [("BBQ Bacon Burger", 1), ("Pomfrit", 2)],
     OrderStatus.PENDING, None, "Savska cesta 32, Zagreb", ago(minutes=17)),

    # ---- Accepted: courier pool has been pinged --------------------------
    ("marija@demo.hr", "zen@demo.hr", [("California Maki (8 kom)", 2), ("Miso juha", 2)],
     OrderStatus.ACCEPTED, None, "Maksimirska 120, Zagreb", ago(minutes=26)),
    ("luka@demo.hr", "green@demo.hr", [("Quinoa Bowl", 1), ("Zeleni smoothie", 1)],
     OrderStatus.ACCEPTED, None, "Heinzelova 62, Zagreb", ago(minutes=33)),

    # ---- Preparing -------------------------------------------------------
    ("petra@demo.hr", "napoli@demo.hr", [("Capricciosa", 1), ("Quattro Formaggi", 1)],
     OrderStatus.PREPARING, None, "Trg bana Jelacica 5, Zagreb", ago(minutes=41)),
    (TEST_LOGIN, TEST_LOGIN, [("Test Burger", 2), ("Test Salata", 1)],
     OrderStatus.PREPARING, None, "Ilica 242, Zagreb", ago(minutes=48)),

    # ---- Ready: waiting for a courier to claim them ----------------------
    ("ana@demo.hr", "burgerbar@demo.hr", [("Cheeseburger", 2), ("Onion Rings", 1)],
     OrderStatus.READY, None, "Vukovarska 15, Zagreb", ago(hours=1, minutes=5)),
    ("ivan@demo.hr", "dolce@demo.hr", [("New York Cheesecake", 2), ("Espresso", 2)],
     OrderStatus.READY, None, "Savska cesta 32, Zagreb", ago(hours=1, minutes=14)),
    ("marija@demo.hr", "zen@demo.hr", [("Ramen Tonkotsu", 1), ("Gyoza (5 kom)", 1)],
     OrderStatus.READY, None, "Maksimirska 120, Zagreb", ago(hours=1, minutes=22)),

    # ---- Picked up: courier en route -------------------------------------
    (TEST_LOGIN, TEST_LOGIN, [("Test Pizza", 2), ("Test Sok", 1)],
     OrderStatus.PICKED_UP, TEST_LOGIN, "Ilica 242, Zagreb", ago(hours=1, minutes=40)),
    ("luka@demo.hr", "napoli@demo.hr", [("Vegetariana", 1), ("Margherita", 1)],
     OrderStatus.PICKED_UP, "josip@demo.hr", "Heinzelova 62, Zagreb",
     ago(hours=1, minutes=52)),

    # ---- Delivered history -----------------------------------------------
    (TEST_LOGIN, TEST_LOGIN, [("Test Salata", 1), ("Test Sok", 1)],
     OrderStatus.DELIVERED, TEST_LOGIN, "Ilica 242, Zagreb", ago(days=1, hours=3)),
    ("ana@demo.hr", "zen@demo.hr", [("Sashimi Mix", 1), ("Sake Nigiri (6 kom)", 2)],
     OrderStatus.DELIVERED, TEST_LOGIN, "Vukovarska 15, Zagreb", ago(days=1, hours=6)),
    ("petra@demo.hr", "burgerbar@demo.hr", [("Classic Burger", 3), ("Pomfrit", 3)],
     OrderStatus.DELIVERED, "nikola@demo.hr", "Trg bana Jelacica 5, Zagreb",
     ago(days=2, hours=2)),
    ("ivan@demo.hr", "napoli@demo.hr", [("Capricciosa", 2)],
     OrderStatus.DELIVERED, "josip@demo.hr", "Savska cesta 32, Zagreb",
     ago(days=3, hours=5)),
    ("marija@demo.hr", "green@demo.hr", [("Falafel Wrap", 2), ("Humus s pitom", 1)],
     OrderStatus.DELIVERED, "ines@demo.hr", "Maksimirska 120, Zagreb",
     ago(days=4, hours=1)),
    ("luka@demo.hr", "dolce@demo.hr", [("Palacinke (3 kom)", 2), ("Sladoled (kugla)", 3)],
     OrderStatus.DELIVERED, "nikola@demo.hr", "Heinzelova 62, Zagreb",
     ago(days=5, hours=7)),
    ("ana@demo.hr", "burgerbar@demo.hr", [("Veggie Burger", 1), ("Onion Rings", 2)],
     OrderStatus.DELIVERED, "ines@demo.hr", "Vukovarska 15, Zagreb",
     ago(days=7, hours=4)),

    # ---- Terminal edge cases ---------------------------------------------
    ("petra@demo.hr", "zen@demo.hr", [("Ramen Tonkotsu", 2)],
     OrderStatus.CANCELLED, None, "Trg bana Jelacica 5, Zagreb", ago(days=1, hours=9)),
    ("ivan@demo.hr", "green@demo.hr", [("Caesar salata", 1)],
     OrderStatus.REJECTED, None, "Savska cesta 32, Zagreb", ago(days=2, hours=8)),
]

# How long after creation each status was reached (drives updated_at) and
# whether the courier pool ping is still sitting unread in the dispatch feed.
STATUS_META = {
    OrderStatus.PENDING: (0, None),
    OrderStatus.ACCEPTED: (3, False),
    OrderStatus.PREPARING: (6, False),
    OrderStatus.READY: (18, False),
    OrderStatus.PICKED_UP: (25, True),
    OrderStatus.DELIVERED: (47, True),
    OrderStatus.CANCELLED: (5, None),
    OrderStatus.REJECTED: (4, None),
}


# ---------------------------------------------------------------------------
def reset(db) -> None:
    """Empty the demo tables and restart the id sequences at 1."""
    if engine.dialect.name == "postgresql":
        db.execute(text(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE"))
    else:  # pragma: no cover - the stack runs on Postgres
        for model in (OrderItem, CourierPing, Order, Product, Customer, Partner, Worker):
            db.query(model).delete()
    db.commit()


def seed(db) -> dict[str, int]:
    customers: dict[str, Customer] = {}
    for spec in CUSTOMERS:
        customers[spec["email"]] = Customer(
            name=spec["name"],
            email=spec["email"],
            phone=spec.get("phone"),
            hashed_password=pw(spec.get("password", DEMO_PASSWORD)),
            is_active=spec.get("is_active", True),
            created_at=ago(days=30),
        )
    db.add_all(customers.values())

    workers: dict[str, Worker] = {}
    for spec in WORKERS:
        workers[spec["email"]] = Worker(
            name=spec["name"],
            email=spec["email"],
            phone=spec.get("phone"),
            specialty=spec.get("specialty"),
            hashed_password=pw(spec.get("password", DEMO_PASSWORD)),
            is_active=True,
            created_at=ago(days=30),
        )
    db.add_all(workers.values())

    partners: dict[str, Partner] = {}
    for spec in PARTNERS:
        partners[spec["contact_email"]] = Partner(
            company_name=spec["company_name"],
            contact_email=spec["contact_email"],
            phone=spec.get("phone"),
            hashed_password=pw(spec.get("password", DEMO_PASSWORD)),
            is_active=True,
            created_at=ago(days=30),
        )
    db.add_all(partners.values())

    # Ids are needed below: products and orders reference them as plain ints.
    db.flush()

    # menu[partner_email][product_name] -> Product
    menu: dict[str, dict[str, Product]] = {}
    for spec in PARTNERS:
        owner = partners[spec["contact_email"]]
        menu[spec["contact_email"]] = {}
        for name, description, price, available in spec["menu"]:
            product = Product(
                partner_id=owner.id,
                name=name,
                description=description,
                price=Decimal(price),
                is_available=available,
                created_at=ago(days=29),
            )
            menu[spec["contact_email"]][name] = product
            db.add(product)
    db.flush()

    orders = 0
    pings = 0
    for cust_email, part_email, lines, status, courier, address, created in ORDERS:
        order = Order(
            customer_id=customers[cust_email].id,
            partner_id=partners[part_email].id,
            worker_id=workers[courier].id if courier else None,
            status=status.value,
            delivery_address=address,
            created_at=created,
        )

        total = Decimal("0.00")
        for product_name, quantity in lines:
            product = menu[part_email][product_name]
            order.items.append(
                OrderItem(
                    product_id=product.id,
                    product_name=product.name,      # snapshot, as the API does
                    unit_price=product.price,       # snapshot
                    quantity=quantity,
                )
            )
            total += product.price * quantity
        order.total_amount = total

        minutes, ping_acked = STATUS_META[status]
        order.updated_at = created + timedelta(minutes=minutes)
        db.add(order)
        orders += 1

        # A ping is dropped into the courier pool the moment a partner accepts,
        # so every order that got past PENDING has one.
        if ping_acked is not None:
            db.flush()  # need order.id
            db.add(
                CourierPing(
                    order_id=order.id,
                    partner_id=order.partner_id,
                    delivery_address=order.delivery_address,
                    acknowledged=ping_acked,
                    created_at=created + timedelta(minutes=3),
                )
            )
            pings += 1

    db.commit()
    return {
        "customers": len(customers),
        "partners": len(partners),
        "workers": len(workers),
        "products": sum(len(m) for m in menu.values()),
        "orders": orders,
        "courier_pings": pings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--keep",
        action="store_true",
        help="append instead of wiping the demo tables first",
    )
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if args.keep:
            print("--keep: postojeci podaci ostaju, dodajem na njih.")
        else:
            print("Brisem demo tablice i krecem ispocetka...")
            reset(db)
        counts = seed(db)
    finally:
        db.close()

    print("\nGotovo. Uneseno:")
    for name, count in counts.items():
        print(f"  {count:>4}  {name}")

    print(f"""
Prijava (svi racuni: lozinka "{DEMO_PASSWORD}")

  Customer  http://localhost:18001/docs    ana@demo.hr, ivan@demo.hr, ...
  Worker    http://localhost:18002/docs    josip@demo.hr, nikola@demo.hr, ines@demo.hr
  Partner   http://localhost:18003/docs    napoli@demo.hr, zen@demo.hr, ...
  Frontend  http://localhost:13000

Test racun na SVE tri usluge:  email "{TEST_LOGIN}"  /  lozinka "{TEST_PASSWORD}"
""")


if __name__ == "__main__":
    main()
