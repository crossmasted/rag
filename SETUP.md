# 部署指南（拿到代码后必读）

本项目**不包含**体积庞大的运行环境和模型文件（约 20 GB），需要你按下面 3 步自行准备。
全部完成后双击 `start_all.bat` 即可使用，无需 Docker。

## 前置要求

- Windows 10 / 11
- 磁盘预留约 25 GB（模型 + 运行环境）
- 建议有 NVIDIA 显卡（4 GB 显存以上）；没有也能跑，但只能走 CPU，速度会慢很多
- MySQL 8.x（登录功能必需，见第 4 步）

---

## 第 1 步：下载三个便携组件

把下载的文件解压到项目 `tools\` 下的对应位置（**目录名必须一致**）：

| 组件 | 下载地址 | 解压目标位置 | 关键文件 |
| --- | --- | --- | --- |
| Ollama | https://ollama.com/download/windows | `tools\ollama\` | `tools\ollama\ollama.exe` |
| Qdrant | https://github.com/qdrant/qdrant/releases | `tools\qdrant\` | `tools\qdrant\qdrant.exe` |
| Node.js 20 | https://nodejs.org/dist/v20.18.0/node-v20.18.0-win-x64.zip | `tools\node20\node-v20.18.0-win-x64\` | `tools\node20\node-v20.18.0-win-x64\node.exe` |

> Ollama 官方的 Windows 安装包是安装器，装完后把 `ollama.exe` 复制过来即可（或者用 zip 版）。
> Node 必须是 20.x：系统的旧版 Node（如 14）会让 Vite 启动报 `Unexpected token '??='`。

---

## 第 2 步：下载并导入模型

### 2.1 下载 GGUF 文件

| 模型 | 用途 | 存放位置 |
| --- | --- | --- |
| qwen2.5-3b-instruct-q4_k_m.gguf | 生成回答 | `tools\models\qwen2.5-3b\` |
| bge-m3-FP16.gguf | 文本向量化 | `tools\models\bge-m3\` |

推荐从 ModelScope（国内速度快）或 Hugging Face 下载。

### 2.2 导入到 Ollama

先在另一个窗口启动 Ollama（或直接双击 `start_ollama.bat`），然后：

```bat
cd tools\ollama
set OLLAMA_MODELS=%~dp0..\ollama-data

ollama create bge-m3 -f ..\models\bge-m3\Modelfile
ollama create qwen2.5:3b -f ..\models\qwen2.5-3b\Modelfile
```

验证：

```bat
ollama list
```

应能看到 `qwen2.5:3b` 和 `bge-m3` 两个模型。

> 如果换用 7B 模型：`tools\models\qwen2.5-7b\` 是多分片 GGUF，Modelfile 里**必须为每个分片各写一行 `FROM`**，
> 否则报 `invalid split GGUF ... has 1 shards, expected 2`。

---

## 第 3 步：安装依赖并启动

### 3.1 后端

```bat
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

> 需要 Python 3.10+（本项目在 3.13 上验证过）。

### 3.2 前端

```bat
cd frontend
..\tools\node20\node-v20.18.0-win-x64\npm.cmd install
```

### 3.3 启动

回到项目根目录，双击：

```
start_all.bat
```

脚本会依次打开 5 个窗口（MySQL / Ollama / Qdrant / 后端 / 前端），等待服务就绪后**自动把两个模型预加载进显存**，
然后访问 http://localhost:5173 注册账号并登录后即可提问。

停止全部服务：双击 `stop_all.bat`。

---

## 第 4 步：MySQL 初始化（登录功能必需）

登录功能把用户账号存在 MySQL 里，首次使用前需要建库和建应用账号（只需执行一次）：

1. 启动 MySQL：双击 `start_mysql.bat`（如果 MySQL 不在 `D:\MySQL\mysql-8.0.26-winx64`，先编辑脚本里的 `MYSQL_HOME`）。
2. 用 root 进入控制台：

```bat
D:\MySQL\mysql-8.0.26-winx64\bin\mysql.exe -uroot -p
```

3. 输入你的 root 密码后，执行下面 4 条语句：

```sql
CREATE DATABASE IF NOT EXISTS rag_kb DEFAULT CHARACTER SET utf8mb4;
CREATE USER IF NOT EXISTS 'rag'@'localhost' IDENTIFIED BY 'rag_pass';
GRANT ALL PRIVILEGES ON rag_kb.* TO 'rag'@'localhost';
FLUSH PRIVILEGES;
```

4. 复制 `.env.example` 为 `.env`，按需修改 MySQL 与 JWT 配置（`.env` 已被 .gitignore 排除，不会上传）。
   - `MYSQL_*` 与本项目 `.env` 默认值一致时无需改动。
   - `JWT_SECRET` 改成随机长字符串（生产环境必改）。
5. 忘了 root 密码？MySQL 官方 `--init-file` 方式重置，不要用 `skip-grant-tables`（8.0.26 在 Windows 上会禁掉 TCP 连接）。

---

## 常见问题

| 现象 | 原因与解决 |
| --- | --- |
| 提问报「连接失败，请重试」 | 服务还没启动完。等 `start_all.bat` 提示 All services ready 后再提问 |
| 登录/注册时报数据库连接失败 | MySQL 没启动（先开 `start_mysql.bat`），或 `.env` 的 `MYSQL_*` 与第 4 步建的不一致 |
| 后端窗口一闪而过 | .bat 被改坏了。脚本必须是 **CRLF 换行 + 纯 ASCII**，否则中文路径会让 cmd 解析错乱 |
| 回答很慢（几十秒） | 没走 GPU。检查 `nvidia-smi` 驱动版本 ≥ 530；4 GB 显存可同时放下 3b + bge-m3 |
| `Unexpected token '??='` | Node 版本太低，必须用 `tools\node20` 里的 Node 20 |
| 首次提问特别慢 | 模型首次加载进显存的一次性开销，第二次提问就快了 |