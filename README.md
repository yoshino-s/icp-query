# ICP 备案查询服务

一个基于 FastAPI 的 ICP 备案信息查询服务，通过自动化验证码识别技术，实现对工信部备案查询系统的自动化查询。

## 📋 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [工作原理](#工作原理)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [API 文档](#api-文档)
- [Docker 部署](#docker-部署)
- [开发说明](#开发说明)
- [常见问题](#常见问题)

## ✨ 功能特性

- 🔍 **自动化查询**：自动识别并破解工信部验证码，实现全自动备案信息查询
- 💾 **结果缓存**：使用 SQLite 数据库缓存查询结果，提高查询效率
- 🎯 **验证码池**：智能管理验证码认证信息，提高系统稳定性
- 🚀 **高性能**：基于 FastAPI 异步框架，支持高并发查询
- 🐳 **容器化部署**：提供 Docker 镜像，一键部署
- 🔧 **GPU 加速**：支持 ONNX Runtime GPU 加速，提升验证码识别速度

## 🛠 技术栈

### 核心框架
- **FastAPI**: 现代化的 Python Web 框架
- **SQLModel**: 基于 SQLAlchemy 的 ORM 框架
- **SQLite**: 轻量级数据库

### 验证码识别
- **ddddocr**: 目标检测模型，用于识别验证码中的目标位置
- **ONNX Runtime**: 深度学习推理引擎，运行 Siamese 网络模型进行图像匹配
- **OpenCV**: 图像处理库

### 其他依赖
- **httpx**: 异步 HTTP 客户端
- **Pydantic**: 数据验证和序列化
- **FastAPI CLI**: 内置的服务器启动工具

## 🔬 工作原理

### 整体架构

```
┌─────────────┐
│  客户端请求  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  FastAPI 服务   │
└──────┬──────────┘
       │
       ├──► 检查缓存 ──► SQLite 数据库
       │
       └──► 未命中缓存
              │
              ▼
       ┌──────────────────┐
       │  验证码池管理     │
       │  (AuthPool)      │
       └──────┬───────────┘
              │
              ▼
       ┌──────────────────┐
       │  获取验证码       │
       └──────┬───────────┘
              │
              ▼
       ┌──────────────────┐
       │  验证码识别流程   │
       │  1. 目标检测     │
       │  2. 图像匹配     │
       │  3. 坐标加密     │
       └──────┬───────────┘
              │
              ▼
       ┌──────────────────┐
       │  查询备案信息     │
       └──────┬───────────┘
              │
              ▼
       ┌──────────────────┐
       │  保存到缓存      │
       └──────────────────┘
```

### 验证码识别流程

1. **获取验证码图片**
   - 从工信部 API 获取大图（背景图）和小图（滑块图）

2. **目标检测**
   - 使用 ddddocr 检测大图中的 5 个目标位置
   - 通过背景差分算法去除背景干扰

3. **图像匹配**
   - 使用 Siamese 网络模型（ONNX）进行图像相似度匹配
   - 将小图中的 4 个位置与检测到的目标进行匹配
   - 匹配阈值：0.7

4. **坐标加密**
   - 将匹配成功的坐标进行 AES 加密
   - 使用服务器提供的密钥进行加密

5. **提交验证**
   - 将加密后的坐标提交给服务器验证
   - 获取认证签名用于后续查询

### 验证码池机制

系统使用 `AuthPool` 管理验证码认证信息：

- **预生成**：系统启动时预先生成验证码认证信息
- **复用**：查询完成后将认证信息返回池中，供后续使用
- **自动补充**：当池为空时，自动生成新的认证信息
- **线程安全**：使用异步锁保证并发安全

## 🚀 快速开始

### 环境要求

- Python >= 3.11.3
- 操作系统：Linux / macOS / Windows

### 安装步骤

1. **克隆项目**

```bash
git clone <repository-url>
cd icp-query
```

2. **安装依赖**

使用 `uv`（推荐）：

```bash
uv sync
```

或使用 `pip`：

```bash
pip install -r requirements.txt
```

3. **准备模型文件**

确保项目根目录存在 `siamese.onnx` 模型文件。

4. **配置数据库**

编辑 `config.yaml`：

```yaml
logging:
  level: "INFO"
database:
  dsn: "sqlite+aiosqlite:///./icp_records.db"
```

5. **启动服务**

**开发环境**：

使用 `fastapi dev`（推荐，支持自动重载）：

```bash
fastapi dev icp_query.app:app
```

**生产环境**：

使用 `fastapi run`：

```bash
fastapi run icp_query.app:app --host 0.0.0.0 --port 8000
```

### 验证安装

访问 `http://localhost:8000/docs` 查看 API 文档，或测试查询接口：

```bash
curl "http://localhost:8000/query?name=北京百度网讯科技有限公司"
```

## ⚙️ 配置说明

### config.yaml

```yaml
# 日志配置
logging:
  level: "DEBUG"  # 可选: DEBUG, INFO, WARNING, ERROR

# 数据库配置
database:
  dsn: "sqlite+aiosqlite:///./icp_records.db"  # SQLite 数据库路径
  pool_size: 5      # 连接池大小
  max_overflow: 10  # 最大溢出连接数
```

### 环境变量

- `USE_ONNX_CUDA`: 控制是否使用 GPU 加速
  - 设置为 `0`、`false` 或 `no` 时禁用 GPU（即使可用）
  - 默认：自动检测并使用可用的 GPU

## 📚 API 文档

### 1. 查询备案信息

**端点**: `GET /query`

**参数**:
- `name` (string, required): 要查询的单位名称或域名

**响应**:
```json
{
  "cached": false,
  "record": {
    "id": 1,
    "domain": "example.com",
    "unit_name": "示例公司",
    "main_licence": "京ICP备12345678号",
    "service_licence": "京ICP备12345678号-1",
    "content_type_name": "互联网信息服务",
    "nature_name": "企业",
    "leader_name": "张三",
    "limit_access": false,
    "main_id": 123456,
    "service_id": 789012,
    "update_record_time": "2024-01-01T00:00:00"
  }
}
```

**示例**:
```bash
curl "http://localhost:8000/query?name=北京百度网讯科技有限公司"
```

### 2. 获取验证码认证信息

**端点**: `GET /solve_captcha`

**响应**:
```json
{
  "uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "auth": "encrypted_sign_string"
}
```

**示例**:
```bash
curl "http://localhost:8000/solve_captcha"
```

### 错误响应

**404 Not Found**: 未找到备案信息
```json
{
  "detail": "not found"
}
```

**500 Internal Server Error**: 服务器内部错误（如验证码识别失败）

## 🐳 Docker 部署

### 构建镜像

```bash
docker build -t icp-query:latest .
```

### 运行容器

```bash
docker run -d \
  --name icp-query \
  -p 8000:8000 \
  -v $(pwd)/icp_records.db:/app/icp_records.db \
  icp-query:latest
```

### Docker Compose

创建 `docker-compose.yml`:

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

启动服务：

```bash
docker-compose up -d
```

## 💻 开发说明

### 项目结构

```
icp-query/
├── icp_query/              # 主应用目录
│   ├── api/               # API 相关模块
│   │   ├── miit.py        # 工信部 API 客户端
│   │   └── crack.py       # 验证码识别模块
│   ├── db/                # 数据库模块
│   │   ├── db.py          # 数据库模型和连接
│   │   ├── query.py       # 查询操作
│   │   └── config.py      # 数据库配置
│   ├── dao/               # 数据访问层
│   │   └── query.py       # 查询响应模型
│   ├── app.py             # FastAPI 应用入口
│   ├── config.py          # 配置管理
│   └── logging.py         # 日志配置
├── scripts/               # 工具脚本
│   ├── fetch.py           # 验证码数据采集脚本
│   └── process_images.py # 图像处理脚本
├── data/                  # 数据目录
│   ├── big/               # 大图样本
│   ├── small/             # 小图样本
│   └── medium/            # 背景模板
├── config.yaml            # 配置文件
├── siamese.onnx          # Siamese 网络模型
├── requirements.txt       # Python 依赖
├── Dockerfile            # Docker 镜像定义
└── README.md             # 项目文档
```

### 开发环境设置

1. **安装开发依赖**

```bash
uv sync --group dev
```

2. **代码格式化**

```bash
ruff format .
ruff check .
```

3. **运行应用**

```bash
# 开发模式（支持自动重载）
fastapi dev icp_query.app:app
```

### 数据采集

如果需要更新验证码样本数据：

```bash
python scripts/fetch.py
```

### GPU 支持

#### 检查 GPU 可用性

```bash
python -c "import onnxruntime; print(onnxruntime.get_available_providers())"
```

#### 启用 GPU 加速

1. **安装 GPU 版本的 ONNX Runtime**

```bash
pip install onnxruntime-gpu
```

2. **设置环境变量**

```bash
export USE_ONNX_CUDA=1
```

或禁用 GPU（强制使用 CPU）：

```bash
export USE_ONNX_CUDA=0
```

## ❓ 常见问题

### Q: 验证码识别失败怎么办？

A: 
1. 检查 `siamese.onnx` 模型文件是否存在
2. 检查背景模板图片是否完整（`data/medium/` 目录）
3. 查看日志了解具体错误信息
4. 尝试重新训练或更新模型

### Q: 查询速度慢？

A:
1. 启用 GPU 加速（如果可用）
2. 增加验证码池大小
3. 使用缓存避免重复查询
4. 使用进程管理器（如 systemd、supervisor）运行多个服务实例以提高并发能力

### Q: 如何更新模型？

A:
1. 将新的 `siamese.onnx` 文件替换旧文件
2. 确保模型输入输出格式匹配
3. 重启服务

### Q: 数据库文件位置？

A: 默认位置为项目根目录下的 `icp_records.db`。可以通过 `config.yaml` 中的 `database.dsn` 配置修改。

### Q: 支持哪些数据库？

A: 当前版本使用 SQLite，但可以通过修改 `database.dsn` 配置使用其他 SQLAlchemy 支持的数据库（如 PostgreSQL、MySQL）。

## 📝 许可证

本项目采用 [MIT License](LICENSE) 许可证。

**重要免责声明**：

本项目仅供学习和研究使用。使用本软件时，您需要：

- ✅ 遵守所有适用的法律法规
- ✅ 遵守目标网站的服务条款和使用协议
- ✅ 确保使用方式符合相关法律法规要求
- ✅ 承担使用本软件的全部责任和风险

**作者和贡献者不对以下情况承担责任**：

- ❌ 任何非法或未经授权的使用
- ❌ 因使用或滥用本软件导致的任何法律后果
- ❌ 对任何第三方服务造成的任何影响或损害

使用本软件即表示您已阅读、理解并同意遵守上述条款，并承担使用本软件的全部责任。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

[添加联系方式]

---

**⚠️ 法律声明**: 本项目仅供学习和研究使用。使用本软件前，请仔细阅读 [LICENSE](LICENSE) 文件中的完整免责声明。使用本软件即表示您同意承担所有相关法律责任。
