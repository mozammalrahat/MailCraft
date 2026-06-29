from app.db.models import Scenario, get_session_factory
from app.services.auth_service import hash_password, register_user, verify_password


def test_register_user_creates_default_scenarios() -> None:
    factory = get_session_factory()
    db = factory()
    try:
        user = register_user(db, "test@example.com", "password123")
        scenarios = db.query(Scenario).filter(Scenario.user_id == user.id).all()
        assert len(scenarios) == 6
        assert user.email == "test@example.com"
    finally:
        db.close()


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)
