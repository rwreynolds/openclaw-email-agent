import pytest


class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestAccountsEndpoint:
    def test_list_accounts_empty(self, client):
        response = client.get("/accounts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestEmailsEndpoint:
    def test_list_emails(self, client):
        response = client.get("/emails")
        assert response.status_code == 200
        data = response.json()
        assert "emails" in data
        assert "total" in data

    def test_list_emails_with_filters(self, client):
        response = client.get("/emails?unread_only=true&limit=10")
        assert response.status_code == 200


class TestThreadsEndpoint:
    def test_list_threads(self, client):
        response = client.get("/threads")
        assert response.status_code == 200
        data = response.json()
        assert "threads" in data
        assert "total" in data

    def test_get_thread_not_found(self, client):
        response = client.get("/threads/nonexistent-thread-id")
        assert response.status_code == 404


class TestSchedulerEndpoints:
    def test_scheduler_status(self, client):
        response = client.get("/scheduler/status")
        assert response.status_code == 200
        data = response.json()
        assert "running" in data
