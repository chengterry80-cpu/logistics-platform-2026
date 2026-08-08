# 前端部署与运行指南 - 无车承运智能物流平台

## 一、技术栈

| 模块 | 版本/选型 | 用途 |
| :--- | :--- | :--- |
| 核心框架 | Vue 3.4.x | 渐进式前端框架 |
| 构建工具 | Vite 5.x | 极速启动与 HMR |
| 路由 | Vue Router 4.x | 前端路由 + 角色权限控制 |
| 状态管理 | Pinia 2.x (persist 插件) | 用户信息持久化 |
| UI 组件库 | Element Plus 2.x + 图标库 | 中后台 UI |
| HTTP 客户端 | Axios 1.6.x | API 请求 + JWT 拦截器 |
| 日期工具 | Day.js | 时间格式化 |

## 二、前端目录结构

```
frontend/
├── index.html                    # Vite 入口 HTML
├── package.json                  # 依赖声明 (dev/build 脚本)
├── vite.config.js                # Vite 配置（含 /api 代理到 8000 端口）
└── src/
    ├── main.js                   # 应用入口（Vue/ElementPlus/Pinia/Router）
    ├── App.vue                   # 根组件（ConfigProvider + <router-view>）
    ├── styles/
    │   └── main.css              # 全局样式
    ├── api/
    │   ├── request.js            # axios 实例 + JWT 请求/响应拦截器
    │   └── index.js              # 所有业务 API 函数封装（40+ 个）
    ├── store/
    │   └── user.js               # Pinia 用户状态（token/roleCode/持久化）
    ├── router/
    │   └── index.js              # 路由表 + 角色权限守卫（beforeEach）
    ├── layouts/
    │   └── MainLayout.vue        # 主布局：顶栏 + 按角色动态侧边栏
    └── views/
        ├── login/index.vue       # 登录页（含快速角色切换）
        ├── dashboard/index.vue   # 工作台（4 角色通用，按角色变卡片/快捷操作）
        ├── shipper/              # === 货主端 ===
        │   ├── requests.vue          # 运输需求列表/筛选/取消
        │   ├── request-form.vue      # 发布/编辑运输需求
        │   ├── quotes.vue            # 报价列表 + 接受/拒绝
        │   └── tasks.vue             # 运输任务跟踪 + 确认完成/付款
        ├── carrier/              # === 承运商端 ===
        │   ├── market.vue            # 需求广场（浏览+报价弹窗）
        │   ├── quotes.vue            # 我的报价
        │   ├── tasks.vue             # 运输任务+指派司机车辆+异常上报
        │   ├── drivers.vue           # 司机 CRUD
        │   ├── vehicles.vue          # 车辆 CRUD
        │   └── loading-plan.vue      # 智能装车推荐（三维占位 + 方案明细）
        ├── driver/               # === 司机端 ===
        │   ├── tasks.vue             # 我的任务（开始运输/更新位置/送达/异常）
        │   └── location.vue          # 位置上报页（支持 1 分钟自动上报）
        └── admin/                # === 管理员端 ===
            ├── users.vue             # 用户管理（4 角色）
            ├── requests.vue          # 全量需求管理
            ├── quotes.vue            # 全量报价管理
            ├── tasks.vue             # 全量任务 + 异常监控
            └── logs.vue              # 状态流转日志（StateLog）
```

## 三、启动命令

### 3.1 后端（Django REST Framework）

在仓库根目录执行：

```powershell
# （首次）初始化演示账号，密码 logistics123
python manage.py init_demo_accounts

# 启动服务
python manage.py runserver 127.0.0.1:8000
```

启动后可访问：

| 服务 | 地址 |
| :--- | :--- |
| 后端 API | http://127.0.0.1:8000/api/ |
| JWT 登录 | http://127.0.0.1:8000/api/token/ |
| JWT 刷新 | http://127.0.0.1:8000/api/token/refresh/ |
| Django Admin | http://127.0.0.1:8000/admin/ |

### 3.2 前端（Vite）

在 `frontend/` 子目录执行：

```powershell
cd frontend
npm install      # 首次安装依赖
npm run dev      # 启动开发服务器，端口 5173
```

访问 http://localhost:5173/，Vite 已内置 `/api` 代理到 `http://127.0.0.1:8000`，无需处理跨域。

**生产构建：**

```powershell
npm run build      # 产物输出到 dist/
npm run preview    # 本地预览 dist/
```

## 四、演示账号（所有账号统一密码：`logistics123`）

| 角色 | 用户名 | 可访问功能模块 |
| :--- | :--- | :--- |
| 管理员 | `admin` | 用户、需求、报价、任务、日志 全局管理 |
| 货主 | `shipper01` | 发布需求 → 查看报价 → 确认报价 → 跟踪任务 → 确认付款 |
| 承运商 | `carrier01` | 需求广场报价 → 指派司机车辆 → 装车推荐 → 任务管理 |
| 司机 | `driver01` | 我的任务、开始运输、位置上报、确认送达、异常上报 |
| 司机 | `driver02` | 同上（备用于车辆 京B66666 / 京C99999） |

## 五、前后端对接约定

1. **统一响应格式：** 后端统一返回 `{ code: 0, data: ..., message: 'success' }`，
   前端 `request.js` 拦截器仅在 `code === 0` 时拆包返回 `data`，否则抛错。
   （SimpleJWT `/token/` 例外，直接返回裸 `{access,refresh}`，拦截器已兼容。）
2. **JWT 认证：** 所有业务请求在 `Authorization: Bearer <access>` 中携带 token；
   响应 401 自动清空登录态并跳 `/login`。
3. **角色路由权限：** 路由 `meta.roles` 声明可访问角色，`beforeEach` 守卫拒绝越权访问。
4. **列表分页接口：** 返回 `{ count, next, previous, results }`，前端通用表格直接消费。

## 六、初始化命令清单（一键环境）

```powershell
# 1. 后端
python manage.py migrate
python manage.py init_demo_accounts
python manage.py runserver 127.0.0.1:8000

# 2. 前端（另开终端）
cd frontend
npm install
npm run dev
```

完成后在浏览器打开 http://localhost:5173/ ，使用上表任一账号登录即可。
