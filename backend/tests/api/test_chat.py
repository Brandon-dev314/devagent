
class TestRoot:

    def test_root_returns_200(self, client):
     
        response = client.get("/")

        assert response.status_code == 200

    def test_root_contains_app_info(self, client):
      
        data = client.get("/").json()

        assert "app" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
        assert data["app"] == "DevAgent"

    def test_root_shows_docs_url_in_debug(self, client):

        data = client.get("/").json()
        assert data["docs"] == "/docs"


class TestLiveness:


    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_alive_status(self, client):
        data = client.get("/health").json()
        assert data["status"] == "alive"

    def test_health_includes_version(self, client):

        data = client.get("/health").json()
        assert "version" in data
        assert data["version"]  # No vacío


class TestReadiness:


    def test_readiness_returns_200(self, client):
        response = client.get("/health/ready")
        assert response.status_code == 200

    def test_readiness_includes_checks(self, client):
        data = client.get("/health/ready").json()

        assert "checks" in data
        assert "postgres" in data["checks"]
        assert "redis" in data["checks"]
        assert "qdrant" in data["checks"]

    def test_readiness_reports_status(self, client):
    
        data = client.get("/health/ready").json()
        assert data["status"] in ("ready", "degraded")


class TestDocs:

    def test_swagger_docs_available_in_debug(self, client):

        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema_available(self, client):

        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "DevAgent"