# 🚀 FastPPT 部署文档

> 完整的 Docker 容器化部署指南，适用于生产环境

## 📋 目录

- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [服务管理](#服务管理)
- [性能优化](#性能优化)
- [监控和维护](#监控和维护)
- [故障排查](#故障排查)

---

## 环境要求

### Docker 版本

- **Docker**: >= 20.10.0
- **Docker Compose**: >= 2.0.0

验证安装：
```bash
docker --version
docker compose version
```

### 系统要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核 | 4 核+ |
| 内存 | 4 GB | 8 GB+ |
| 磁盘 | 20 GB | 50 GB+ |
| 操作系统 | Linux/macOS/Windows | Ubuntu 22.04 LTS |

### 端口要求

确保以下端口未被占用：

| 服务 | 端口 | 说明 |
|------|------|------|
| FastAPI 后端 | 8000 | API 服务 |
| PPTXGenJS | 3000 | PPT 生成服务 |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存 |
| Prometheus Metrics | 9090 | 监控指标 |

检查端口占用：
```bash
# Linux/macOS
netstat -tuln | grep -E '8000|3000|5432|6379|9090'

# Windows
netstat -ano | findstr "8000 3000 5432 6379 9090"
```

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/your-org/FastPPT.git
cd FastPPT
```

### 2. 配置环境变量

复制环境变量模板并编辑：

```bash
cd docker
cp .env.example .env
nano .env  # 或使用你喜欢的编辑器
```

**必填配置**（至少需要配置这些）：

```bash
# API Keys（必填）
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx

# 数据库密码（建议修改）
POSTGRES_PASSWORD=your_secure_password_here
REDIS_PASSWORD=your_redis_password_here
```

### 3. 一键启动

```bash
cd docker
docker compose up -d
```

### 4. 验证部署

等待所有服务启动（约 30-60 秒），然后检查状态：

```bash
docker compose ps
```

预期输出：
```
NAME                   STATUS              PORTS
fastppt-backend        Up (healthy)        0.0.0.0:8000->8000/tcp
fastppt-pptxgenjs      Up (healthy)        0.0.0.0:3000->3000/tcp
fastppt-postgres       Up (healthy)        0.0.0.0:5432->5432/tcp
fastppt-redis          Up (healthy)        0.0.0.0:6379->6379/tcp
```

**测试 API 连接**：

```bash
# 健康检查
curl http://localhost:8000/health

# 预期返回
{"status":"healthy","timestamp":"2026-04-21T15:30:00Z"}

# API 文档
curl http://localhost:8000/docs
# 在浏览器中打开: http://localhost:8000/docs
```

**测试 PPTXGenJS 服务**：

```bash
curl http://localhost:3000/health

# 预期返回
{"status":"ok","service":"pptxgenjs"}
```

部署成功！现在可以启动前端或使用 API。

---

## 配置说明

### 环境变量详解

#### API Keys（必填）

```bash
# DeepSeek API - 用于 LLM 对话生成
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
# 获取地址: https://platform.deepseek.com/

# DashScope API - 用于 Embedding 向量化
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx
# 获取地址: https://dashscope.console.aliyun.com/
```

#### RAGFlow 配置（可选）

如果使用外部 RAGFlow 服务：

```bash
RAGFLOW_BASE_URL=https://your-ragflow-instance.com
RAGFLOW_API_KEY=your_ragflow_api_key_here
RAGFLOW_KB_ID=your_knowledge_base_id_here
```

留空则使用内置 TF-IDF 检索（推荐新手使用）。

#### 数据库配置

```bash
# PostgreSQL
POSTGRES_DB=fastppt              # 数据库名
POSTGRES_USER=fastppt            # 用户名
POSTGRES_PASSWORD=change_me      # 密码（生产环境必改）
POSTGRES_PORT=5432               # 端口

# Redis
REDIS_PASSWORD=change_me         # 密码（生产环境必改）
REDIS_PORT=6379                  # 端口
RAG_CACHE_TTL=3600              # 缓存过期时间（秒）
```

#### 应用配置

```bash
APP_ENV=production               # 环境: development/production
LOG_LEVEL=info                   # 日志级别: debug/info/warning/error
BACKEND_PORT=8000                # 后端端口
PPTXGENJS_PORT=3000             # PPT 服务端口
METRICS_PORT=9090               # 监控端口
```

#### CORS 配置

```bash
# 允许的前端域名（逗号分隔）
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,https://your-domain.com
```

#### 监控配置

```bash
ENABLE_METRICS=true              # 启用 Prometheus 指标
```

---

## 服务管理

### 启动服务

```bash
cd docker

# 启动所有服务
docker compose up -d

# 启动指定服务
docker compose up -d fastapi postgres redis
```

### 停止服务

```bash
# 停止所有服务
docker compose stop

# 停止指定服务
docker compose stop fastapi
```

### 重启服务

```bash
# 重启所有服务
docker compose restart

# 重启指定服务
docker compose restart fastapi
```

### 完全停止并删除

```bash
# 停止并删除容器（保留数据卷）
docker compose down

# 停止并删除容器和数据卷（危险！会删除数据库数据）
docker compose down -v
```

### 查看日志

```bash
# 查看所有服务日志
docker compose logs -f

# 查看指定服务日志
docker compose logs -f fastapi

# 查看最近 100 行
docker compose logs --tail=100 fastapi

# 查看特定时间段
docker compose logs --since 2026-04-21T10:00:00 fastapi
```

### 健康检查

```bash
# 检查所有服务状态
docker compose ps

# 检查后端健康
curl http://localhost:8000/health

# 检查 PPTXGenJS 健康
curl http://localhost:3000/health

# 检查 PostgreSQL
docker compose exec postgres pg_isready -U fastppt

# 检查 Redis
docker compose exec redis redis-cli --raw incr ping
```

### 更新服务

```bash
# 拉取最新代码
git pull

# 重新构建并启动
cd docker
docker compose up -d --build

# 仅重新构建后端
docker compose up -d --build fastapi
```

### 进入容器调试

```bash
# 进入后端容器
docker compose exec fastapi bash

# 进入数据库容器
docker compose exec postgres psql -U fastppt -d fastppt

# 进入 Redis 容器
docker compose exec redis redis-cli
```

---

## 性能优化

### 资源配置建议

编辑 `docker-compose.yml`，为服务添加资源限制：

```yaml
services:
  fastapi:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

### 推荐配置

| 服务 | CPU 限制 | 内存限制 | 说明 |
|------|---------|---------|------|
| fastapi | 2.0 | 2G | 主要计算负载 |
| pptxgenjs | 1.0 | 1G | PPT 生成 |
| postgres | 1.0 | 1G | 数据库 |
| redis | 0.5 | 512M | 缓存 |

### 缓存配置

优化 Redis 缓存提升性能：

```bash
# 在 .env 中调整
RAG_CACHE_TTL=7200              # 增加缓存时间到 2 小时
```

Redis 配置优化（编辑 `docker-compose.yml`）：

```yaml
redis:
  command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD} --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### 并发设置

调整 FastAPI workers 数量（编辑 `docker/Dockerfile.backend`）：

```dockerfile
# 默认 4 workers
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# 高并发场景（8 核 CPU）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "8"]
```

**Workers 计算公式**：
```
workers = (2 × CPU 核心数) + 1
```

### PostgreSQL 优化

编辑 `docker-compose.yml` 添加性能参数：

```yaml
postgres:
  command: postgres -c shared_buffers=256MB -c max_connections=200 -c effective_cache_size=1GB
```

---

## 监控和维护

### Prometheus Metrics

FastAPI 后端暴露 Prometheus 指标在 `http://localhost:9090/metrics`。

**查看指标**：

```bash
curl http://localhost:9090/metrics
```

**关键指标**：

| 指标名 | 说明 |
|--------|------|
| `http_requests_total` | 总请求数 |
| `http_request_duration_seconds` | 请求耗时 |
| `http_requests_in_progress` | 进行中的请求 |
| `system_cpu_usage` | CPU 使用率 |
| `system_memory_usage` | 内存使用率 |

### 日志查看

**应用日志**：

```bash
# 实时查看后端日志
docker compose logs -f fastapi

# 查看错误日志
docker compose logs fastapi | grep ERROR

# 导出日志到文件
docker compose logs fastapi > fastapi.log
```

**日志文件位置**：

- 后端日志：`backend/logs/fastppt.log`
- PPTXGenJS 日志：容器内 `/app/logs/`

**查看容器内日志**：

```bash
# 进入容器查看
docker compose exec fastapi cat /app/logs/fastppt.log

# 实时监控
docker compose exec fastapi tail -f /app/logs/fastppt.log
```

### 备份策略

#### 数据库备份

```bash
# 备份 PostgreSQL
docker compose exec postgres pg_dump -U fastppt fastppt > backup_$(date +%Y%m%d).sql

# 恢复备份
docker compose exec -T postgres psql -U fastppt fastppt < backup_20260421.sql
```

#### Redis 备份

```bash
# 触发 Redis 保存
docker compose exec redis redis-cli --raw SAVE

# 备份 RDB 文件
docker compose cp redis:/data/dump.rdb ./backup/redis_$(date +%Y%m%d).rdb
```

#### 文件备份

```bash
# 备份上传文件和生成的文件
tar -czf backup_files_$(date +%Y%m%d).tar.gz backend/uploads backend/outputs
```

#### 自动备份脚本

创建 `backup.sh`：

```bash
#!/bin/bash
BACKUP_DIR="./backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 备份数据库
docker compose exec postgres pg_dump -U fastppt fastppt > $BACKUP_DIR/db.sql

# 备份 Redis
docker compose exec redis redis-cli --raw SAVE
docker compose cp redis:/data/dump.rdb $BACKUP_DIR/redis.rdb

# 备份文件
tar -czf $BACKUP_DIR/files.tar.gz backend/uploads backend/outputs

echo "Backup completed: $BACKUP_DIR"
```

设置定时任务（crontab）：
```bash
# 每天凌晨 2 点备份
0 2 * * * /path/to/FastPPT/backup.sh
```

---

## 故障排查

### 常见问题

#### 1. 容器启动失败

**症状**：`docker compose ps` 显示服务 `Exit 1` 或 `Restarting`

**排查步骤**：

```bash
# 查看容器日志
docker compose logs fastapi

# 检查配置文件
cat docker/.env

# 验证环境变量
docker compose config
```

**常见原因**：
- API Key 未配置或无效
- 端口被占用
- 数据库连接失败

#### 2. 数据库连接失败

**症状**：日志显示 `could not connect to server` 或 `connection refused`

**解决方案**：

```bash
# 检查 PostgreSQL 是否运行
docker compose ps postgres

# 检查健康状态
docker compose exec postgres pg_isready -U fastppt

# 重启数据库
docker compose restart postgres

# 查看数据库日志
docker compose logs postgres
```

#### 3. Redis 连接失败

**症状**：日志显示 `Redis connection error` 或 `NOAUTH Authentication required`

**解决方案**：

```bash
# 检查 Redis 状态
docker compose ps redis

# 测试连接（需要密码）
docker compose exec redis redis-cli -a your_redis_password ping

# 检查密码配置
grep REDIS_PASSWORD docker/.env

# 重启 Redis
docker compose restart redis
```

#### 4. API 返回 500 错误

**症状**：前端请求返回 `Internal Server Error`

**排查步骤**：

```bash
# 查看详细错误日志
docker compose logs fastapi | grep ERROR

# 检查 API Key 是否有效
curl -H "Authorization: Bearer $DEEPSEEK_API_KEY" https://api.deepseek.com/v1/models

# 进入容器手动测试
docker compose exec fastapi python -c "import os; print(os.getenv('DEEPSEEK_API_KEY'))"
```

#### 5. 端口冲突

**症状**：`Error starting userland proxy: listen tcp4 0.0.0.0:8000: bind: address already in use`

**解决方案**：

```bash
# 查找占用端口的进程
# Linux/macOS
lsof -i :8000

# Windows
netstat -ano | findstr :8000

# 修改端口（编辑 .env）
BACKEND_PORT=8001

# 重新启动
docker compose up -d
```

#### 6. 磁盘空间不足

**症状**：容器无法写入文件，日志显示 `No space left on device`

**解决方案**：

```bash
# 检查磁盘使用
df -h

# 清理 Docker 未使用的资源
docker system prune -a

# 清理旧的日志文件
find backend/logs -name "*.log" -mtime +30 -delete

# 清理旧的输出文件
find backend/outputs -name "*.pptx" -mtime +7 -delete
```

#### 7. 内存不足

**症状**：容器被 OOM Killer 杀死，日志显示 `Killed`

**解决方案**：

```bash
# 检查内存使用
docker stats

# 增加 swap 空间（Linux）
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 或减少 workers 数量（编辑 Dockerfile.backend）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

### 调试技巧

#### 启用调试日志

```bash
# 修改 .env
LOG_LEVEL=debug

# 重启服务
docker compose restart fastapi
```

#### 查看实时资源使用

```bash
# 实时监控所有容器
docker stats

# 监控特定容器
docker stats fastppt-backend fastppt-postgres
```

#### 网络诊断

```bash
# 检查容器网络
docker network ls
docker network inspect fastppt-network

# 测试容器间连接
docker compose exec fastapi ping postgres
docker compose exec fastapi curl http://pptxgenjs:3000/health
```

#### 完全重置

如果遇到无法解决的问题，可以完全重置：

```bash
# 停止并删除所有容器和数据
docker compose down -v

# 清理 Docker 缓存
docker system prune -a

# 删除本地文件
rm -rf backend/uploads/* backend/outputs/* backend/logs/*

# 重新启动
docker compose up -d --build
```

---

## 附录

### 快速命令参考

```bash
# 启动
docker compose up -d

# 停止
docker compose stop

# 重启
docker compose restart

# 查看日志
docker compose logs -f

# 查看状态
docker compose ps

# 健康检查
curl http://localhost:8000/health

# 进入容器
docker compose exec fastapi bash

# 备份数据库
docker compose exec postgres pg_dump -U fastppt fastppt > backup.sql

# 更新服务
docker compose up -d --build
```

### 生产环境检查清单

部署到生产环境前，确保完成以下检查：

- [ ] 修改所有默认密码（POSTGRES_PASSWORD, REDIS_PASSWORD）
- [ ] 配置有效的 API Keys（DEEPSEEK_API_KEY, DASHSCOPE_API_KEY）
- [ ] 设置正确的 CORS_ORIGINS（包含实际域名）
- [ ] 配置 HTTPS 反向代理（Nginx/Caddy）
- [ ] 设置防火墙规则（仅开放必要端口）
- [ ] 配置自动备份脚本
- [ ] 设置日志轮转（logrotate）
- [ ] 配置监控告警（Prometheus + Alertmanager）
- [ ] 测试备份恢复流程
- [ ] 准备应急预案

### 推荐的生产环境架构

```
Internet
    ↓
[Nginx/Caddy] (HTTPS, 反向代理)
    ↓
[FastAPI Backend] ← [PPTXGenJS]
    ↓           ↓
[PostgreSQL]  [Redis]
```

### 获取帮助

- **文档**: `docs/` 目录
- **API 文档**: http://localhost:8000/docs
- **问题反馈**: GitHub Issues
- **技术支持**: support@example.com

---

**部署完成！** 🎉

现在你可以开始使用 FastPPT 了。如有问题，请参考故障排查章节或联系技术支持。
