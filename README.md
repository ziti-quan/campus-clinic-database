# 校园医务室信息管理系统

基于 Flask + Flask-SQLAlchemy + MySQL 的课程大作业，包含三个相互独立的应用：

| 应用 | 角色 | 主要功能 |
|---|---|---|
| `app.py` | 患者端 | 注册 / 登录 / 按科室与日期查号源 / 挂号 / 查我的挂号、病历、药单 |
| `app_D.py` | 医生端 | 登录 / 查看就诊患者 / 书写病历 / 开具处方 / 查历史处方与个人排班 |
| `admin.py` | 管理端 | 科室、医生、药品、排班的管理 |

## 项目亮点

- **完整的数据库设计**：8 张关系表，覆盖 科室 → 医生 → 排班 → 挂号 → 处方 → 处方明细 的完整链路，含 E-R 图、关系模式、范式分析与数据字典。
- **把业务规则下沉到数据库层**：9 个外键（含一条复合外键）、5 个唯一约束、9 个 CHECK 约束，实测 9 类非法写入全部被数据库拒绝。
- **有意为之的反范式设计**：区分“键值型冗余”（靠外键级联更新同步）与“快照型冗余”（刻意冻结，保证历史处方与挂号单不被后续修改改变），并有调价实验佐证。
- **事务与并发控制方案**：挂号扣号源、开方扣库存均采用“条件更新 + 事务”，消除超卖与库存负数。
- **可复现的验证材料**：`数据库验证报告.html` 与 `截图/` 下的 20 张界面截图，全部由运行中的系统真实产生。

## 目录结构

```
数据库大作业源码/
├── app.py                  患者端入口
├── app_D.py                医生端入口
├── admin.py                管理端入口
├── config.py               统一配置（数据库连接、会话密钥，从环境变量 / .env 读取）
├── .env.example            配置模板，复制为 .env 后填写
├── .gitignore
├── schema.sql              数据库结构（8 张表，必须先执行）
├── seed_data.sql           演示数据
├── 数据库设计说明.md        需求分析、E-R 图、数据字典、约束与代码冲突分析
├── 数据库验证报告.html      表结构、外键、索引、约束实测结果
├── 实验报告_校园医务室数据库.docx
├── ER图.png                E-R 图
├── ER图源码/                E-R 图渲染脚本（陈氏记法）与导出的 PNG / SVG
├── requirements.txt        依赖清单
├── 截图/                    运行截图与验证图
├── 截图工具/                一键自动截取前端界面的脚本
├── static/                 css / js
│   ├── css/  (style, auth, doctor, doctor_login, admin)
│   └── js/   (script, auth, doctor, doctor_dashboard, prescribe_medicine, admin)
└── templates/
    ├── index.html  login.html  register.html                 患者端
    ├── doctor_login.html  doctor_dashboard.html              医生端
    ├── patient_record.html  prescribe_medicine.html  error.html
    └── admin.html                                            管理端
```

## 环境要求

- Python 3.9+
- MySQL 8.0（5.7 也可运行，但 CHECK 约束不生效）或 MariaDB 10.4+
- 依赖见 `requirements.txt`

## 初始化步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库连接

连接信息统一由 `config.py` 管理，**不写在源码里**。把配置模板复制成 `.env` 再填写自己的信息即可：

```bash
cp .env.example .env        # Windows 命令行可用 copy .env.example .env
```

```ini
# .env
DB_HOST=localhost
DB_PORT=3308
DB_NAME=hospital
DB_USER=root
DB_PASSWORD=你的MySQL口令
SECRET_KEY=随机字符串
DOCTOR_SECRET_KEY=另一个随机字符串
```

`.env` 已加入 `.gitignore`，不会被提交。会话密钥可以用
`python -c "import secrets; print(secrets.token_hex(32))"` 生成。

> 口令中若含 `@`、`#`、`/` 等字符无需手工转义，`config.py` 会自动做 URL 编码。

### 3. 建库建表（务必执行，不要依赖 `db.create_all()`）

```bash
mysql -h 127.0.0.1 -P 3308 -u root -p < schema.sql
```

脚本会创建 `hospital` 库与 8 张表，并**先删除同名旧表**（可重复执行）。

### 4. 导入演示数据

```bash
mysql -h 127.0.0.1 -P 3308 -u root -p hospital < seed_data.sql
```

排班日期按 `CURDATE() + N 天` 动态生成，因此无论哪天导入，患者端都能查到未来 5 天的号源。

### 5. 启动三个服务（必须使用不同端口）

三个应用默认都监听 5000，需改端口后再同时启动：

```bash
python app.py                    # 患者端 http://127.0.0.1:5000
python app_D.py                  # 医生端（改为 5001）
python admin.py                  # 管理端（改为 5002）
```

### 6. 连通性自检

访问 `http://127.0.0.1:5000/test_db`，显示"数据库连接成功！"即为正常。

## 演示账号

| 端 | 账号 | 密码 |
|---|---|---|
| 患者端 | 手机号 `13800138000`（陈晨） / `13900139000`（赵雪） | `123456` |
| 医生端 | 姓名 `张伟` / `李娜` / `王强` / `刘敏` | `123456` |
| 管理端 | 直接访问首页，无登录 | — |

## 重要提醒

1. **必须先执行 `schema.sql` 再启动应用。** 三个应用的 SQLAlchemy 模型定义彼此不一致，`db.create_all()` 只会按当前文件创建表，谁先启动就把结构定死，另外两个应用随即报错（详见《数据库设计说明.md》第 7 节）。
2. **医生端登录目前是明文口令比对**，因此 `doctor.D_password` 存的是明文；患者端相反，存的是 werkzeug 哈希。两者不可互换。这是已知不足，改进方向见设计说明第 9 节。
3. 删除医生、科室、药品时，若已有排班或挂号引用，会被外键的 `ON DELETE RESTRICT` 拦截并报错，这是预期的数据保护行为，不是程序故障。
4. 管理端目前没有登录鉴权，属于课程作业范围内的已知不足，正式使用前需要补充。

## 安全说明

- 数据库口令与会话密钥均通过环境变量或 `.env` 注入，源码中不含任何凭据；`.env` 已被 `.gitignore` 忽略。
- 演示数据中的患者、医生、手机号均为虚构，口令统一为 `123456`，仅用于本地演示。
- 患者口令以 werkzeug 哈希存储；医生端仍为明文比对，是已知不足。
- 已知不足与改进方向集中记录在 `数据库设计说明.md` 第 9 节。

## 数据库设计文档

数据库的完整设计（需求分析、E-R 图、关系模式与范式分析、索引与约束设计、数据字典、事务与并发方案、安全建议）见 `数据库设计说明.md`。
