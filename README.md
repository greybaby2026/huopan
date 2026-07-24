# 令将货盘系统

男装货盘管理系统。内网部署，Lucky 穿透外网访问。

## 快速启动

### 生产模式 (单端口, 推荐)

```bash
# 1. 构建前端
cd huopan/frontend
npm install
npm run build

# 2. 启动后端 (含前端SPA)
cd ../backend
pip install -r requirements.txt
set PYTHONPATH=.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8767

# 3. 首次访问 http://localhost:8767/login
#    点击"初始化管理员账号" -> 用 admin/admin123 登录
```

或双击 `start.bat`。

### 开发模式 (前后端分离)

双击 `dev.bat`，或：
```bash
# 终端1 - 后端
cd backend
set PYTHONPATH=.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8767 --reload

# 终端2 - 前端 (热更新)
cd frontend
npx vite --host 0.0.0.0 --port 5173
```

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python FastAPI + SQLAlchemy + SQLite |
| 前端 | Vue 3 + TypeScript + Element Plus + VxeTable + Univer |
| Excel导出 | openpyxl (支持图片嵌入 + 水印) |
| Excel导入 | openpyxl (模板下载 + 批量导入) |
| 图片处理 | Pillow (缩略图 + 品牌水印) |
| 认证 | Token (SHA256 密码哈希, 8h过期) |

## 功能模块

### ✅ 已完成

- **产品库**: CRUD、多条件检索、图片上传(批量/缩略图)、批量改价/上下架、Excel批量导入
- **客户管理**: 客户CRUD、客户分级(A/B/C级)、折扣率、起订量
- **货盘管理**: 按客户级别批量生成货盘、专属定价、库存状态、价格历史
- **Excel双模式**: VxeTable数据网格(批量操作) + Univer电子表格(自由排版)
- **一键导出**: Excel(含产品图嵌入+水印) + 图片包(zip+水印)
- **图片水印**: 导出时自动加"令将货盘"品牌水印
- **多用户权限**: 管理员/业务员/仓库, token认证, 路由守卫
- **生产部署**: 前端构建后由FastAPI单端口托管, Lucky穿透

### 默认账号

首次部署后访问 `/login`, 点击"初始化管理员账号":
- 用户名: `admin`
- 密码: `admin123`

## 数据库

SQLite (`backend/huopan.db`)，零运维。可迁 PostgreSQL，改 `.env` 中 `DATABASE_URL`。

### 核心表

| 表 | 说明 |
|----|------|
| users | 系统用户 (admin/sales/warehouse) |
| products | 产品 (款号/品类/颜色/价格/库存) |
| product_images | 产品图片 (原图+缩略图) |
| customers | 客户 |
| customer_levels | 客户分级 (折扣率/起订量) |
| catalogs | 货盘 (客户×产品×专属价格) |
| price_history | 价格变更记录 |

## Lucky 穿透

见 `LUCKY_DEPLOY.md`

## API 文档

启动后访问 `http://localhost:8767/docs` (Swagger UI)
