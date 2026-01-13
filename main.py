from datetime import datetime
from typing import Dict, List

from fastapi import FastAPI, HTTPException, status

from models import Task, TaskCreate, TaskUpdate

app = FastAPI(
    title="To-Do List",
    description="Create REST API"
)

tasks_db: Dict[int, Task] = {}
next_id: int = 1


@app.get("/")
def root():
    return {
        "message": "To-Do List",
        "endpoints": {
            "GET /tasks": "Get all tasks",
            "GET /tasks/{id}": "Get task by ID",
            "POST /tasks": "Create new task",
            "PUT /tasks/{id}": "Update task",
            "DELETE /tasks/{id}": "Delete task"
        }
    }

@app.get("/tasks", response_model=List[Task], status_code=status.HTTP_200_OK)
def get_tasks(completed: bool=None):
    if completed is None:
        return list(tasks_db.values())
    results = []
    for task in tasks_db.values():
        if task.completed == completed:
            results.append(task)
    return results

@app.get("/tasks/{task_id}", response_model=Task, status_code=status.HTTP_200_OK)
def get_task(task_id: int):
    if task_id not in tasks_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error: Task with the id {task_id} not found"
        )
    return tasks_db[task_id]

@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(task_data: TaskCreate):
    global next_id

    new_task = Task(
        id=next_id,
        title=task_data.title,
        description=task_data.description,
        completed=False,
        created_at=datetime.now(),
        updated_at=datetime.now()

    )

    tasks_db[next_id] = new_task
    next_id += 1
    return new_task

@app.put("/tasks/{task_id}", response_model=Task, status_code=status.HTTP_200_OK)
def update_task(task_id: int, task_data: TaskUpdate):
    if task_id not in tasks_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with the id {task_id} not found"
        )
    task = tasks_db[task_id]
    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    task.updated_at = datetime.now()
    return task

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    if task_id not in tasks_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with the id {task_id} not found"
        )
    del tasks_db[task_id]
    return None

