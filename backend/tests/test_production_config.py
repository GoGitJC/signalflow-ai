from app.core.config import Settings
from app.core.startup import ProductionConfigError, validate_production_settings


def test_cors_origins_list_parsing(monkeypatch):
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://www.example.com, https://app.example.com",
    )
    monkeypatch.setenv("SIGNALFLOW_FRONTEND_ORIGIN", "https://www.example.com")
    settings = Settings()
    assert settings.cors_origin_list == [
        "https://www.example.com",
        "https://app.example.com",
    ]


def test_database_url_render_normalization(monkeypatch):
    monkeypatch.setenv(
        "SIGNALFLOW_DATABASE_URL",
        "postgresql://user:pass@host:5432/signalflow",
    )
    settings = Settings()
    assert settings.database_url.startswith("postgresql+psycopg://")


def test_production_validation_rejects_localhost_cors(monkeypatch):
    monkeypatch.setenv("SIGNALFLOW_ENVIRONMENT", "production")
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "secret")
    monkeypatch.setenv("SIGNALFLOW_CREDENTIAL_ENCRYPTION_KEY", "key")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "true")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173")
    monkeypatch.setenv("APP_PUBLIC_API_URL", "https://api.example.com")
    settings = Settings()
    try:
        validate_production_settings(settings)
        raised = False
    except ProductionConfigError:
        raised = True
    assert raised
