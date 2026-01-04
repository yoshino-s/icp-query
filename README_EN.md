<div align="center">

# ICP Record Query Service

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com)
[![Code style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

[中文](README.md) | **English**

An ICP record query service based on FastAPI, enabling automated querying of the MIIT (Ministry of Industry and Information Technology) record system through automated captcha recognition technology.

[Features](#-features) • [Quick Start](#-quick-start) • [API Documentation](#-api-documentation) • [License](#-license)

</div>

---

## 📋 Table of Contents

<details>
<summary>Click to expand</summary>

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [How It Works](#-how-it-works)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [API Documentation](#-api-documentation)
- [Docker Deployment](#-docker-deployment)
- [Development](#-development)
- [FAQ](#-faq)
- [License](#-license)

</details>

---

## ✨ Features

- 🔍 **Automated Querying**: Automatically recognizes and solves MIIT captchas for fully automated ICP record queries
- 💾 **Result Caching**: Uses SQLite database to cache query results, improving query efficiency
- 🎯 **Captcha Pool**: Intelligently manages captcha authentication information to improve system stability
- 🚀 **High Performance**: Based on FastAPI async framework, supports high-concurrency queries
- 🐳 **Containerized Deployment**: Provides Docker image for one-click deployment
- 🔧 **GPU Acceleration**: Supports ONNX Runtime GPU acceleration to improve captcha recognition speed

---

## 🛠 Tech Stack

### Core Framework
- **FastAPI**: Modern Python web framework
- **SQLModel**: ORM framework based on SQLAlchemy
- **SQLite**: Lightweight database

### Captcha Recognition
- **ddddocr**: Object detection model for identifying target positions in captchas
- **ONNX Runtime**: Deep learning inference engine running Siamese network model for image matching
- **OpenCV**: Image processing library

### Other Dependencies
- **httpx**: Async HTTP client
- **Pydantic**: Data validation and serialization
- **FastAPI CLI**: Built-in server startup tool

---

## 🔬 How It Works

### Overall Architecture

```
┌─────────────┐
│Client Request│
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  FastAPI Service│
└──────┬──────────┘
       │
       ├──► Check Cache ──► SQLite Database
       │
       └──► Cache Miss
              │
              ▼
       ┌──────────────────┐
       │ Captcha Pool      │
       │ Management        │
       │ (AuthPool)        │
       └──────┬───────────┘
              │
              ▼
       ┌──────────────────┐
       │   Get Captcha    │
       └──────┬───────────┘
              │
              ▼
       ┌──────────────────┐
       │ Captcha Recognition│
       │ 1. Object Detection│
       │ 2. Image Matching  │
       │ 3. Coordinate Encrypt│
       └──────┬───────────┘
              │
              ▼
       ┌──────────────────┐
       │ Query ICP Record  │
       └──────┬───────────┘
              │
              ▼
       ┌──────────────────┐
       │  Save to Cache   │
       └──────────────────┘
```

### Captcha Recognition Process

1. **Get Captcha Images**
   - Fetch large image (background) and small image (slider) from MIIT API

2. **Object Detection**
   - Use ddddocr to detect 5 target positions in the large image
   - Remove background interference through background subtraction algorithm

3. **Image Matching**
   - Use Siamese network model (ONNX) for image similarity matching
   - Match 4 positions in the small image with detected targets
   - Matching threshold: 0.7

4. **Coordinate Encryption**
   - Encrypt successfully matched coordinates using AES
   - Use server-provided key for encryption

5. **Submit Verification**
   - Submit encrypted coordinates to server for verification
   - Obtain authentication signature for subsequent queries

### Captcha Pool Mechanism

The system uses `AuthPool` to manage captcha authentication information:

- **Pre-generation**: Pre-generate captcha authentication information at system startup
- **Reuse**: Return authentication information to the pool after query completion for subsequent use
- **Auto-replenishment**: Automatically generate new authentication information when the pool is empty
- **Thread-safe**: Use async locks to ensure concurrency safety

---

## 🚀 Quick Start

### Requirements

- Python >= 3.11.3
- OS: Linux / macOS / Windows

### Installation

#### 1. Clone Repository

```bash
git clone <repository-url>
cd icp-query
```

#### 2. Install Dependencies

**Using `uv` (Recommended):**

```bash
uv sync
```

**Or using `pip`:**

```bash
pip install -r requirements.txt
```

#### 3. Prepare Model File

Ensure the `siamese.onnx` model file exists in the project root directory.

#### 4. Configure Database

Edit `config.yaml`:

```yaml
logging:
  level: "INFO"
database:
  dsn: "sqlite+aiosqlite:///./icp_records.db"
```

#### 5. Start Service

**Development:**

```bash
fastapi dev icp_query.app:app
```

**Production:**

```bash
fastapi run icp_query.app:app --host 0.0.0.0 --port 8000
```

### Verify Installation

Visit `http://localhost:8000/docs` to view API documentation, or test the query endpoint:

```bash
curl "http://localhost:8000/query?name=北京百度网讯科技有限公司"
```

---

## ⚙️ Configuration

### config.yaml

```yaml
# Logging Configuration
logging:
  level: "DEBUG"  # Options: DEBUG, INFO, WARNING, ERROR

# Database Configuration
database:
  dsn: "sqlite+aiosqlite:///./icp_records.db"  # SQLite database path
  pool_size: 5      # Connection pool size
  max_overflow: 10  # Maximum overflow connections
```

### Environment Variables

- `USE_ONNX_CUDA`: Control GPU acceleration
  - Set to `0`, `false`, or `no` to disable GPU (even if available)
  - Default: Automatically detect and use available GPU

---

## 📚 API Documentation

### 1. Query ICP Record

**Endpoint**: `GET /query`

**Parameters**:
- `name` (string, required): Unit name or domain to query

**Response**:
```json
{
  "cached": false,
  "record": {
    "id": 1,
    "domain": "example.com",
    "unit_name": "Example Company",
    "main_licence": "京ICP备12345678号",
    "service_licence": "京ICP备12345678号-1",
    "content_type_name": "Internet Information Service",
    "nature_name": "Enterprise",
    "leader_name": "John Doe",
    "limit_access": false,
    "main_id": 123456,
    "service_id": 789012,
    "update_record_time": "2024-01-01T00:00:00"
  }
}
```

**Example**:
```bash
curl "http://localhost:8000/query?name=北京百度网讯科技有限公司"
```

### 2. Get Captcha Authentication

**Endpoint**: `GET /solve_captcha`

**Response**:
```json
{
  "uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "auth": "encrypted_sign_string"
}
```

**Example**:
```bash
curl "http://localhost:8000/solve_captcha"
```

### Error Responses

**404 Not Found**: ICP record not found
```json
{
  "detail": "not found"
}
```

**500 Internal Server Error**: Internal server error (e.g., captcha recognition failed)

---

## 🐳 Docker Deployment

### Build Image

```bash
docker build -t icp-query:latest .
```

### Run Container

```bash
docker run -d \
  --name icp-query \
  -p 8000:8000 \
  -v $(pwd)/icp_records.db:/app/icp_records.db \
  icp-query:latest
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  icp-query:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./icp_records.db:/app/icp_records.db
      - ./config.yaml:/app/config.yaml
    environment:
      - USE_ONNX_CUDA=1
    restart: unless-stopped
```

Start service:

```bash
docker-compose up -d
```

---

## 💻 Development

### Project Structure

```
icp-query/
├── icp_query/              # Main application directory
│   ├── api/               # API related modules
│   │   ├── miit.py        # MIIT API client
│   │   └── crack.py       # Captcha recognition module
│   ├── db/                # Database module
│   │   ├── db.py          # Database models and connection
│   │   ├── query.py        # Query operations
│   │   └── config.py      # Database configuration
│   ├── dao/               # Data access layer
│   │   └── query.py       # Query response model
│   ├── app.py             # FastAPI application entry
│   ├── config.py          # Configuration management
│   └── logging.py         # Logging configuration
├── scripts/               # Utility scripts
│   ├── fetch.py           # Captcha data collection script
│   └── process_images.py  # Image processing script
├── data/                  # Data directory
│   ├── big/               # Large image samples
│   ├── small/             # Small image samples
│   └── medium/            # Background templates
├── config.yaml            # Configuration file
├── siamese.onnx          # Siamese network model
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker image definition
└── README.md             # Project documentation
```

### Development Setup

#### 1. Install Development Dependencies

```bash
uv sync --group dev
```

#### 2. Code Formatting

```bash
ruff format .
ruff check .
```

#### 3. Run Application

```bash
# Development mode (with auto-reload)
fastapi dev icp_query.app:app
```

### Data Collection

If you need to update captcha sample data:

```bash
python scripts/fetch.py
```

### GPU Support

#### Check GPU Availability

```bash
python -c "import onnxruntime; print(onnxruntime.get_available_providers())"
```

#### Enable GPU Acceleration

1. **Install GPU Version of ONNX Runtime**

```bash
pip install onnxruntime-gpu
```

2. **Set Environment Variable**

```bash
export USE_ONNX_CUDA=1
```

Or disable GPU (force CPU):

```bash
export USE_ONNX_CUDA=0
```

---

## ❓ FAQ

### Q: What if captcha recognition fails?

**A:**
1. Check if `siamese.onnx` model file exists
2. Check if background template images are complete (`data/medium/` directory)
3. Check logs for specific error messages
4. Try retraining or updating the model

### Q: Query is slow?

**A:**
1. Enable GPU acceleration (if available)
2. Increase captcha pool size
3. Use cache to avoid duplicate queries
4. Use process manager (e.g., systemd, supervisor) to run multiple service instances for improved concurrency

### Q: How to update the model?

**A:**
1. Replace old file with new `siamese.onnx` file
2. Ensure model input/output format matches
3. Restart service

### Q: Database file location?

**A:** Default location is `icp_records.db` in the project root directory. Can be modified via `database.dsn` in `config.yaml`.

### Q: Which databases are supported?

**A:** Current version uses SQLite, but can use other SQLAlchemy-supported databases (e.g., PostgreSQL, MySQL) by modifying `database.dsn` configuration.

---

## 📝 License

This project is licensed under the [MIT License](LICENSE).

### Important Disclaimer

This project is for educational and research purposes only. When using this software, you must:

- ✅ Comply with all applicable laws and regulations
- ✅ Comply with the terms of service and usage agreements of target websites
- ✅ Ensure usage complies with relevant legal and regulatory requirements
- ✅ Assume full responsibility and risk for using this software

**Authors and contributors are not responsible for**:

- ❌ Any illegal or unauthorized use
- ❌ Any legal consequences arising from the use or misuse of this software
- ❌ Any impact or damage to any third-party services

By using this software, you acknowledge that you have read, understood, and agree to comply with the above terms and assume full responsibility for using this software.

---

## 🤝 Contributing

Issues and Pull Requests are welcome!

---

## 📧 Contact

[Add contact information]

---

<div align="center">

**⚠️ Legal Notice**: This project is for educational and research purposes only. Before using this software, please carefully read the complete disclaimer in the [LICENSE](LICENSE) file. Using this software indicates your agreement to assume all related legal responsibilities.

Made with ❤️ by the ICP Query Project Contributors

[中文](README.md) | [English](#icp-record-query-service)

</div>

