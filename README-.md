# Task Manager API

A simple CRUD REST API for managing daily tasks, built with **Flask** and **SQLite**.

## Data Model — `Task`

| Field         | Type     | Notes                                      |
|---------------|----------|---------------------------------------------|
| `id`          | integer  | Auto-generated, primary key                |
| `title`       | string   | Required, cannot be empty                  |
| `description` | string   | Optional                                   |
| `status`      | string   | `pending` or `completed` (default: `pending`) |
| `created_at`  | string   | Auto-generated UTC ISO 8601 timestamp      |

## Endpoints

| Method  | Endpoint          | Description                     |
|---------|-------------------|----------------------------------|
| POST    | `/tasks`          | Create a new task                |
| GET     | `/tasks`          | Get all tasks (optional `?status=pending\|completed` filter) |
| GET     | `/tasks/<id>`     | Get a single task by ID           |
| PUT     | `/tasks/<id>`     | Full update (title required)      |
| PATCH   | `/tasks/<id>`     | Partial update (only sent fields change) |
| DELETE  | `/tasks/<id>`     | Delete a task                     |

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/a3limosa000-boop/task-manager-api.git
cd task-manager-api
```

### 2. Create a virtual environment (recommended)
```bash
python3 -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the server
```bash
python app.py
```
The API will start at `http://127.0.0.1:5000`. A `tasks.db` SQLite file is created automatically on first run.

## Example Requests

**Create a task**
```bash
curl -X POST http://127.0.0.1:5000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy groceries", "description": "Milk, eggs, bread"}'
```

**Get all tasks**
```bash
curl http://127.0.0.1:5000/tasks
```

**Get one task**
```bash
curl http://127.0.0.1:5000/tasks/1
```

**Update a task (partial)**
```bash
curl -X PATCH http://127.0.0.1:5000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

**Delete a task**
```bash
curl -X DELETE http://127.0.0.1:5000/tasks/1
```

## Validation & Error Handling

- `title` cannot be empty or missing → `400 Bad Request`
- `status` must be `pending` or `completed` if provided → `400 Bad Request`
- Requesting/updating/deleting a task that doesn't exist → `404 Not Found`
- Malformed JSON body → `400 Bad Request`
- Wrong HTTP method on a route → `405 Method Not Allowed`

All errors are returned as JSON in the form:
```json
{ "error": "Task with id 99 not found." }
```

## Testing

A ready-to-import Postman collection is included: [`postman_collection.json`](./postman_collection.json).
It covers all 6 endpoints plus common error cases (missing title, invalid status, 404s).

To use it:
1. Open Postman → Import → select `postman_collection.json`.
2. Run the server locally (`python app.py`).
3. Run each request in the collection (or use "Run collection" to execute them all).

## Project Structure
```
task-manager-api/
├── app.py                  # Flask application (routes, validation, error handling)
├── requirements.txt        # Python dependencies
├── postman_collection.json # Postman test collection
├── .gitignore
└── README.md
```
