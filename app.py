"""
Task Manager API
-----------------
A simple CRUD API for managing daily tasks, built with Flask + SQLite.

Endpoints:
    POST   /tasks       -> create a task
    GET    /tasks        -> list all tasks
    GET    /tasks/<id>   -> get one task
    PUT    /tasks/<id>   -> full update of a task
    PATCH  /tasks/<id>   -> partial update of a task
    DELETE /tasks/<id>   -> delete a task
"""

from flask import Flask, request, jsonify, g
import sqlite3
import os
from datetime import datetime, timezone

app = Flask(__name__)

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.db")
VALID_STATUSES = ("pending", "completed")


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_db():
    """Open a new database connection if there isn't one yet for this request."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DATABASE) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                description TEXT,
                status      TEXT NOT NULL DEFAULT 'pending',
                created_at  TEXT NOT NULL
            )
            """
        )
        db.commit()


def row_to_task(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "status": row["status"],
        "created_at": row["created_at"],
    }


# ---------------------------------------------------------------------------
# Error handling helpers
# ---------------------------------------------------------------------------
class ApiError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@app.errorhandler(ApiError)
def handle_api_error(err):
    return jsonify({"error": err.message}), err.status_code


@app.errorhandler(404)
def handle_404(err):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(405)
def handle_405(err):
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(500)
def handle_500(err):
    return jsonify({"error": "Internal server error"}), 500


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------
def validate_title(data, required=True):
    if "title" not in data:
        if required:
            raise ApiError("The 'title' field is required.", 400)
        return None
    title = data.get("title")
    if title is None or not str(title).strip():
        raise ApiError("The 'title' field cannot be empty.", 400)
    return str(title).strip()


def validate_status(data):
    if "status" not in data or data.get("status") is None:
        return None
    status = str(data["status"]).strip().lower()
    if status not in VALID_STATUSES:
        raise ApiError(
            f"Invalid 'status' value. Must be one of {VALID_STATUSES}.", 400
        )
    return status


def get_task_or_404(task_id):
    db = get_db()
    row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise ApiError(f"Task with id {task_id} not found.", 404)
    return row


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "message": "Task Manager API is running.",
        "endpoints": {
            "POST /tasks": "Create a new task",
            "GET /tasks": "Retrieve all tasks",
            "GET /tasks/<id>": "Retrieve a specific task",
            "PUT /tasks/<id>": "Fully update a task",
            "PATCH /tasks/<id>": "Partially update a task",
            "DELETE /tasks/<id>": "Delete a task",
        },
    })


@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json(silent=True)
    if data is None:
        raise ApiError("Request body must be valid JSON.", 400)

    title = validate_title(data, required=True)
    description = data.get("description")
    status = validate_status(data) or "pending"
    created_at = datetime.now(timezone.utc).isoformat()

    db = get_db()
    cur = db.execute(
        "INSERT INTO tasks (title, description, status, created_at) VALUES (?, ?, ?, ?)",
        (title, description, status, created_at),
    )
    db.commit()

    row = db.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(row_to_task(row)), 201


@app.route("/tasks", methods=["GET"])
def list_tasks():
    db = get_db()

    status_filter = request.args.get("status")
    if status_filter:
        status_filter = status_filter.strip().lower()
        if status_filter not in VALID_STATUSES:
            raise ApiError(
                f"Invalid 'status' filter. Must be one of {VALID_STATUSES}.", 400
            )
        rows = db.execute(
            "SELECT * FROM tasks WHERE status = ? ORDER BY id", (status_filter,)
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM tasks ORDER BY id").fetchall()

    return jsonify([row_to_task(r) for r in rows]), 200


@app.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    row = get_task_or_404(task_id)
    return jsonify(row_to_task(row)), 200


@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task_full(task_id):
    """Full update: title is required, as with creation."""
    get_task_or_404(task_id)
    data = request.get_json(silent=True)
    if data is None:
        raise ApiError("Request body must be valid JSON.", 400)

    title = validate_title(data, required=True)
    description = data.get("description")
    status = validate_status(data) or "pending"

    db = get_db()
    db.execute(
        "UPDATE tasks SET title = ?, description = ?, status = ? WHERE id = ?",
        (title, description, status, task_id),
    )
    db.commit()

    row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return jsonify(row_to_task(row)), 200


@app.route("/tasks/<int:task_id>", methods=["PATCH"])
def update_task_partial(task_id):
    """Partial update: only provided fields are changed."""
    row = get_task_or_404(task_id)
    data = request.get_json(silent=True)
    if data is None:
        raise ApiError("Request body must be valid JSON.", 400)

    title = row["title"]
    if "title" in data:
        title = validate_title(data, required=True)

    description = row["description"]
    if "description" in data:
        description = data.get("description")

    status = row["status"]
    if "status" in data:
        status = validate_status(data) or status

    db = get_db()
    db.execute(
        "UPDATE tasks SET title = ?, description = ?, status = ? WHERE id = ?",
        (title, description, status, task_id),
    )
    db.commit()

    updated_row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return jsonify(row_to_task(updated_row)), 200


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    get_task_or_404(task_id)
    db = get_db()
    db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    return jsonify({"message": f"Task {task_id} deleted successfully."}), 200


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
else:
    # Ensure DB exists when run via a WSGI server too
    init_db()
