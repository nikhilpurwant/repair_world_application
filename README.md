# RepairWorld Application

This is a simple HTML, JS, Bootstrap And Flask-based application for managing repair requests in the fictional RepairWorld app. The application is created to go along with the [Google ADK - MCP Tutorial]()

---

## 🛠 Features

* persona - customers
  - Create a repair request
  - View all repair requests
  - View a single repair request by ID
* persona repairmen
  - View all repair requests
  - View a single repair request by ID
  - close a repair request

- Uses SQLite for storage
- JWT-based authentication

---

## 🚀 Running Locally

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

#### 2. Start the Flask app
```bash
python app.py
```
Application will be available at http://localhost:5000

API will be available at:
http://localhost:5000/api/repair_requests

🐳 Running with Docker

```bash
docker build -t repairworld-api .
docker run -p 5000:5000 repairworld-api
```
