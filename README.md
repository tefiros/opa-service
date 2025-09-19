# opa-service

# OPA Evaluation Service

This project exposes a simple **FastAPI** service that connects to **OPA (Open Policy Agent)** using the [opa-python-client](https://pypi.org/project/opa-python-client/).
It provides a single endpoint `/evaluate` where you can send input data to evaluate policies registered in OPA.

---

## 🚀 Features

- **POST /evaluate** → Evaluate a policy given its path and input data.
- Uses **FastAPI** for the REST API.
- Uses **opa-python-client** for communication with OPA.
- Includes Docker support and automated tests.

---

## ⚙️ Prerequisites

- Python **3.11+**
- [Poetry](https://python-poetry.org/) for dependency management
- [OPA](https://www.openpolicyagent.org/docs/latest/#running-opa) running in server mode

---

## 🛠️ Setup

Clone the repository and install dependencies:

```bash
git clone https://github.com/your-username/opa-service.git
cd opa-service
poetry install
```

(Optional) activate the virtual environment:

`poetry shell`

---

## ▶️ Running the service

Start the FastAPI service:

`poetry run uvicorn opa_service.main:app --reload`

---

## 🧪 Running Tests

Run the included unit tests:

`poetry run pytest -v `

---

## 🐳 Docker

Build the image:

`docker build -t opa_service . `

Run the container:

`docker run -d -p 8000:8000 opa_service`

## Documentation

You can consult the automatically generated API documentation at:

* Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8001/docs)
* ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8001/redoc)
