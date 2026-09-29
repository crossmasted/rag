# 部署指南（拿到代码后必读）

本项目**不包含**体积庞大的运行环境和模型文件（约 20 GB），需要你按下面 3 步自行准备。
全部完成后双击 `start_all.bat` 即可使用，无需 Docker。

## 前置要求

- Windows 10 / 11
- 磁盘预留约 25 GB（模型 + 运行环境）
- 建议有 NVIDIA 显卡（4 GB 显存以上）；没有也能跑，但只能走 CPU，速度会慢很多

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

脚本会依次打开 4 个窗口（Ollama / Qdrant / 后端 / 前端），等待服务就绪后**自动把两个模型预加载进显存**，
然后访问 http://localhost:5173 即可提问。

停止全部服务：双击 `stop_all.bat`。

---

## 常见问题

| 现象 | 原因与解决 |
| --- | --- |
| 提问报「连接失败，请重试」 | 服务还没启动完。等 `start_all.bat` 提示 All services ready 后再提问 |
| 后端窗口一闪而过 | .bat 被改坏了。脚本必须是 **CRLF 换行 + 纯 ASCII**，否则中文路径会让 cmd 解析错乱 |
| 回答很慢（几十秒） | 没走 GPU。检查 `nvidia-smi` 驱动版本 ≥ 530；4 GB 显存可同时放下 3b + bge-m3 |
| `Unexpected token '??='` | Node 版本太低，必须用 `tools\node20` 里的 Node 20 |
| 首次提问特别慢 | 模型首次加载进显存的一次性开销，第二次提问就快了 |