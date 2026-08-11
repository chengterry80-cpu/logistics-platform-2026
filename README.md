# logistics-platform-2026

无车承运智能物流平台（Django + DRF + Celery + Redis + Vue3）

---

## ⚠️ 安全警告（必读，防止误用已泄露密钥）

> **重要**：本仓库早期历史 commit 中包含一份硬编码的 `settings.py`，
> 其中含有真实的 **MySQL root 密码、Redis 密码 和 Django SECRET_KEY**。
> 这些密钥已视为泄露，**切勿在生产 / 任何公开可访问的服务器上直接使用**。

请至少执行以下操作后再部署：

1. **立即修改真实 MySQL 与 Redis 密码**（如果你的数据库仍然沿用默认密码）
2. **重新生成 Django SECRET_KEY** 并通过 `.env` 注入，参见 `.env.example`
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
3. **不要把真实的 `.env` / 私钥 / 证书 文件提交到 Git**（仓库已经在 `.gitignore` 中屏蔽 `.env`）
4. 如需更彻底清理旧历史，可使用 `git filter-repo` / `BFG Repo-Cleaner` 剔除敏感 commit，或新建一个干净仓库重新推送

---

## 快速开始（本地开发）

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 准备环境变量

```bash
cp .env.example .env
```
然后用文本编辑器修改 `.env`，把 `DB_PASSWORD` / `REDIS_PASSWORD` / `DJANGO_SECRET_KEY` 等值改成你本地的真实值。

### 3. 初始化数据库 & 启动后端

```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```
Swagger 文档：<http://127.0.0.1:8000/api/schema/swagger-ui/>

### 4. 启动前端（另开终端）

```bash
cd frontend
npm install
npm run dev
```
默认访问 <http://127.0.0.1:5173/>

---

## 各角色默认账号（开发演示用）

| 角色 | 用户名 | 密码 | 说明 |
|---|---|---|---|
| 平台管理员 | `admin` | `admin123456` | 后台管理 + 全量 API |
| 货主       | `shipper01` | `Shipper@123` | 发布运单需求、查看报价 |
| 承运商     | `carrier01` | `Carrier@123` | 报价、调度、订单管理 |
| 司机       | `driver01`  | `Driver@123`  | 接单、运输状态更新 |

如需重置密码，可用 `python manage.py changepassword <username>`。
