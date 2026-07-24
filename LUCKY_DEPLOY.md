# Lucky 穿透配置 - 货盘系统外网访问

## 前提

- 内网服务器已运行货盘系统 (后端+前端构建后由 FastAPI 托管, 只需一个端口 8767)
- Lucky 万吉 已部署 (PVE 192.168.1.99:16601)

## 步骤

### 1. 构建前端

```bash
cd huopan/frontend
npm run build
```

构建后 `dist/` 目录由 FastAPI 自动托管, 无需单独跑前端。

### 2. 启动后端

```bash
cd huopan/backend
set PYTHONPATH=.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8767
```

验证: 内网访问 `http://内网IP:8767/` 应看到货盘系统界面。

### 3. Lucky 反向代理配置

登录 Lucky 管理后台 (http://192.168.1.99:16601):

1. **反向代理** -> **添加规则**
2. 配置:
   - 监听端口: 选一个外网可访问端口 (如 8767)
   - 或绑定域名 (如 huopan.yourdomain.com)
   - 后端地址: `http://内网服务器IP:8767`
   - 启用 WebSocket: **是** (Univer 需要)
3. 保存并启用

### 4. 验证外网访问

通过 Lucky 分配的域名/端口访问, 应看到货盘系统界面。

## 生产部署建议

- 用 systemd 或 nssm 将 uvicorn 注册为 Windows 服务, 开机自启
- 数据库从 SQLite 迁移到 PostgreSQL (改 .env 中 DATABASE_URL)
- 定期备份 `huopan.db` 和 `uploads/` 目录
