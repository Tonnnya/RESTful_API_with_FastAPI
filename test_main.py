import pytest
from fastapi.testclient import TestClient
from main import app, tasks_db, next_id
from datetime import datetime


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_database():
    """Clear database before each test"""
    tasks_db.clear()
    # Reset next_id
    import main
    main.next_id = 1
    yield
    # Cleanup after test
    tasks_db.clear()
    main.next_id = 1


class TestRootEndpoint:
    """Tests for root endpoint"""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "endpoints" in data


class TestGetTasks:
    """Tests for GET /tasks endpoint"""

    def test_get_empty_tasks(self, client):
        """Test getting tasks when database is empty"""
        response = client.get("/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_tasks(self, client):
        """Test getting all tasks"""
        # Create test tasks
        client.post("/tasks",
                    json={"title": "Task 1", "description": "Description 1"})
        client.post("/tasks",
                    json={"title": "Task 2", "description": "Description 2"})

        response = client.get("/tasks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "Task 1"
        assert data[1]["title"] == "Task 2"

    def test_get_tasks_filter_completed(self, client):
        """Test filtering tasks by completion status"""
        # Create and complete one task
        client.post("/tasks", json={"title": "Task 1"})
        client.post("/tasks", json={"title": "Task 2"})
        client.put("/tasks/1", json={"completed": True})

        # Get completed tasks
        response = client.get("/tasks?completed=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["completed"] is True

        # Get incomplete tasks
        response = client.get("/tasks?completed=false")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["completed"] is False


class TestGetTaskById:
    """Tests for GET /tasks/{id} endpoint"""

    def test_get_task_by_id(self, client):
        """Test getting a specific task by ID"""
        # Create task
        create_response = client.post("/tasks", json={
            "title": "Test Task",
            "description": "Test Description"
        })
        task_id = create_response.json()["id"]

        # Get task
        response = client.get(f"/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == "Test Task"
        assert data["description"] == "Test Description"

    def test_get_nonexistent_task(self, client):
        """Test getting a task that doesn't exist"""
        response = client.get("/tasks/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestCreateTask:
    """Tests for POST /tasks endpoint"""

    def test_create_task_minimal(self, client):
        """Test creating task with only required fields"""
        response = client.post("/tasks", json={"title": "New Task"})
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["title"] == "New Task"
        assert data["description"] is None
        assert data["completed"] is False
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_task_full(self, client):
        """Test creating task with all fields"""
        response = client.post("/tasks", json={
            "title": "Full Task",
            "description": "Complete description"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Full Task"
        assert data["description"] == "Complete description"
        assert data["completed"] is False

    def test_create_task_auto_increment_id(self, client):
        """Test that IDs auto-increment correctly"""
        response1 = client.post("/tasks", json={"title": "Task 1"})
        response2 = client.post("/tasks", json={"title": "Task 2"})
        response3 = client.post("/tasks", json={"title": "Task 3"})

        assert response1.json()["id"] == 1
        assert response2.json()["id"] == 2
        assert response3.json()["id"] == 3

    def test_create_task_invalid_empty_title(self, client):
        """Test validation: empty title should fail"""
        response = client.post("/tasks", json={"title": ""})
        assert response.status_code == 422

    def test_create_task_invalid_missing_title(self, client):
        """Test validation: missing title should fail"""
        response = client.post("/tasks", json={"description": "No title"})
        assert response.status_code == 422

    def test_create_task_title_too_long(self, client):
        """Test validation: title exceeding max length"""
        long_title = "x" * 201
        response = client.post("/tasks", json={"title": long_title})
        assert response.status_code == 422

    def test_create_task_description_too_long(self, client):
        """Test validation: description exceeding max length"""
        long_description = "x" * 1001
        response = client.post("/tasks", json={
            "title": "Valid title",
            "description": long_description
        })
        assert response.status_code == 422


class TestUpdateTask:
    """Tests for PUT /tasks/{id} endpoint"""

    def test_update_task_title(self, client):
        """Test updating task title"""
        # Create task
        create_response = client.post("/tasks", json={"title": "Original"})
        task_id = create_response.json()["id"]

        # Update title
        response = client.put(f"/tasks/{task_id}", json={"title": "Updated"})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated"

    def test_update_task_description(self, client):
        """Test updating task description"""
        create_response = client.post("/tasks", json={"title": "Task"})
        task_id = create_response.json()["id"]

        response = client.put(f"/tasks/{task_id}",
                              json={"description": "New description"})
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "New description"

    def test_update_task_completed_status(self, client):
        """Test marking task as completed"""
        create_response = client.post("/tasks", json={"title": "Task"})
        task_id = create_response.json()["id"]

        response = client.put(f"/tasks/{task_id}", json={"completed": True})
        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is True

    def test_update_task_partial(self, client):
        """Test partial update (only some fields)"""
        create_response = client.post("/tasks", json={
            "title": "Original",
            "description": "Original description"
        })
        task_id = create_response.json()["id"]

        # Update only title
        response = client.put(f"/tasks/{task_id}", json={"title": "Updated"})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated"
        assert data["description"] == "Original description"

    def test_update_task_multiple_fields(self, client):
        """Test updating multiple fields at once"""
        create_response = client.post("/tasks", json={"title": "Original"})
        task_id = create_response.json()["id"]

        response = client.put(f"/tasks/{task_id}", json={
            "title": "Updated",
            "description": "New description",
            "completed": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated"
        assert data["description"] == "New description"
        assert data["completed"] is True

    def test_update_nonexistent_task(self, client):
        """Test updating a task that doesn't exist"""
        response = client.put("/tasks/999", json={"title": "Updated"})
        assert response.status_code == 404

    def test_update_task_invalid_title(self, client):
        """Test validation on update"""
        create_response = client.post("/tasks", json={"title": "Original"})
        task_id = create_response.json()["id"]

        response = client.put(f"/tasks/{task_id}", json={"title": ""})
        assert response.status_code == 422

    def test_update_task_updates_timestamp(self, client):
        """Test that updated_at timestamp changes"""
        create_response = client.post("/tasks", json={"title": "Task"})
        task_id = create_response.json()["id"]
        original_updated_at = create_response.json()["updated_at"]

        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.01)

        update_response = client.put(f"/tasks/{task_id}",
                                     json={"title": "Updated"})
        new_updated_at = update_response.json()["updated_at"]

        assert new_updated_at != original_updated_at


class TestDeleteTask:
    """Tests for DELETE /tasks/{id} endpoint"""

    def test_delete_task(self, client):
        """Test deleting a task"""
        # Create task
        create_response = client.post("/tasks", json={"title": "To Delete"})
        task_id = create_response.json()["id"]

        # Delete task
        response = client.delete(f"/tasks/{task_id}")
        assert response.status_code == 204

        # Verify task is deleted
        get_response = client.get(f"/tasks/{task_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_task(self, client):
        """Test deleting a task that doesn't exist"""
        response = client.delete("/tasks/999")
        assert response.status_code == 404

    def test_delete_task_removes_from_list(self, client):
        """Test that deleted task is removed from task list"""
        # Create multiple tasks
        client.post("/tasks", json={"title": "Task 1"})
        client.post("/tasks", json={"title": "Task 2"})
        client.post("/tasks", json={"title": "Task 3"})

        # Delete middle task
        client.delete("/tasks/2")

        # Check remaining tasks
        response = client.get("/tasks")
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[1]["id"] == 3