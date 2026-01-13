# 火山方舟大模型服务平台 - 快速入门指南

本指南将帮助您在数分钟内完成首次 API 调用，涵盖环境配置、SDK 安装以及多种模型调用示例。

## 目录

- [火山方舟大模型服务平台 - 快速入门指南](#火山方舟大模型服务平台---快速入门指南)
  - [目录](#目录)
  - [1. 获取并配置 API Key](#1-获取并配置-api-key)
    - [1.1 获取 API Key](#11-获取-api-key)
    - [1.2 配置环境变量](#12-配置环境变量)
  - [2. 开通模型服务](#2-开通模型服务)
  - [3. 安装 SDK](#3-安装-sdk)
    - [3.1 安装方舟 SDK（推荐）](#31-安装方舟-sdk推荐)
    - [3.2 安装 OpenAI SDK（兼容方案）](#32-安装-openai-sdk兼容方案)
  - [4. 发起 API 请求](#4-发起-api-请求)
    - [4.1 文本生成](#41-文本生成)
    - [4.2 多模态理解](#42-多模态理解)
    - [4.3 图片生成](#43-图片生成)
    - [4.4 视频生成（异步调用）](#44-视频生成异步调用)
    - [4.5 工具/插件调用](#45-工具插件调用)
  - [5. 下一步建议](#5-下一步建议)
    - [5.1 平台能力速览](#51-平台能力速览)
    - [5.2 查看完整模型列表](#52-查看完整模型列表)
    - [5.3 深度学习更多功能](#53-深度学习更多功能)
  - [参考链接](#参考链接)
  - [本项目集成说明](#本项目集成说明)
    - [1. 配置环境变量](#1-配置环境变量)
    - [2. 安装依赖](#2-安装依赖)
    - [3. 在前端设置](#3-在前端设置)
    - [4. 支持的模型](#4-支持的模型)

---

## 1. 获取并配置 API Key

### 1.1 获取 API Key

访问 [API Key 管理页面](https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey) 创建您的 API Key。

### 1.2 配置环境变量

建议将 API Key 配置到环境变量中，避免代码中硬编码。

**MacOS / Linux:**

```bash
export ARK_API_KEY="your_api_key_here"
```

**Windows (PowerShell):**

```powershell
$env:ARK_API_KEY = "your_api_key_here"
```

**配置持久化:** 参考 [环境变量配置指南](https://www.volcengine.com/docs/82379/1820161) 进行永久设置。

---

## 2. 开通模型服务

访问 [开通管理页面](https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement) 开通所需的模型服务。

> **提示**: 在使用任何模型前，请确保已在控制台完成模型部署或订阅，获取正确的 `model` ID（例如 `doubao-seed-1-6-251015`）。

---

## 3. 安装 SDK

推荐使用 Python 环境（版本 3.7 或以上）。

### 3.1 安装方舟 SDK（推荐）

```bash
pip install 'volcengine-python-sdk[ark]'
```

### 3.2 安装 OpenAI SDK（兼容方案）

火山方舟也提供 OpenAI 兼容接口，您可以使用 OpenAI SDK 进行调用：

```bash
pip install openai
```

---

## 4. 发起 API 请求

### 4.1 文本生成

用于问答、分析、摘要、翻译等任务。

**使用 Ark SDK:**

```python
import os
from volcenginesdkarkruntime import Ark

client = Ark(
    base_url='https://ark.cn-beijing.volces.com/api/v3',
    api_key=os.getenv('ARK_API_KEY'),
)

response = client.responses.create(
    model="doubao-seed-1-6-251015",  # 替换为您的模型 ID
    input="hello",
    # thinking={"type": "disabled"},  # 可手动禁用深度思考
)
print(response)
```

**使用 OpenAI SDK:**

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=os.getenv('ARK_API_KEY'),
)

response = client.chat.completions.create(
    model="doubao-seed-1-6-251015",  # 替换为您的模型 ID
    messages=[
        {"role": "user", "content": "hello"}
    ]
)
print(response.choices[0].message.content)
```

---

### 4.2 多模态理解

支持图片、视频、PDF 等输入。

```python
import os
from volcenginesdkarkruntime import Ark

client = Ark(
    base_url='https://ark.cn-beijing.volces.com/api/v3',
    api_key=os.getenv('ARK_API_KEY'),
)

response = client.responses.create(
    model="doubao-seed-1-6-251015",
    input=[
        {
            "role": "user",
            "content": [
                {
                    "type": "input_image",
                    "image_url": "https://example.com/image.png",
                },
                {
                    "type": "input_text",
                    "text": "描述这张图片",
                },
            ],
        }
    ]
)
print(response)
```

---

### 4.3 图片生成

基于文本或参考图生成高质量图片。

```python
import os
from volcenginesdkarkruntime import Ark

client = Ark(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=os.getenv('ARK_API_KEY'),
)

images_response = client.images.generate(
    model="doubao-seedream-4-5-251128",
    prompt="一幅充满艺术感的肖像画，柔和的光线照在人物脸上",
    size="2K",
    response_format="url",
    watermark=False
)
print(images_response.data[0].url)
```

---

### 4.4 视频生成（异步调用）

支持文生视频、图生视频等。视频生成为异步任务，需要轮询状态获取结果。

```python
import os
import time
from volcenginesdkarkruntime import Ark

client = Ark(api_key=os.getenv('ARK_API_KEY'))

# 1. 创建视频生成任务
create_result = client.content_generation.tasks.create(
    model="doubao-seedance-1-0-pro-250528",
    content=[{
        "type": "text",
        "text": "一位女性在粉色背景前优雅地旋转",
    }]
)
task_id = create_result.id
print(f"任务已创建，ID: {task_id}")

# 2. 轮询任务状态
while True:
    get_result = client.content_generation.tasks.get(task_id=task_id)
    status = get_result.status
    print(f"当前状态: {status}")
    
    if status == "succeeded":
        print("任务成功!")
        print(get_result)
        break
    elif status == "failed":
        print("任务失败:")
        print(get_result.error)
        break
    
    time.sleep(3)  # 每 3 秒轮询一次
```

---

### 4.5 工具/插件调用

火山方舟支持多种工具调用，如联网搜索、图像处理等。

**联网搜索示例:**

```python
import os
from volcenginesdkarkruntime import Ark

client = Ark(
    base_url='https://ark.cn-beijing.volces.com/api/v3',
    api_key=os.getenv('ARK_API_KEY'),
)

response = client.responses.create(
    model="doubao-seed-1-6-251015",
    input=[{
        "role": "user",
        "content": "北京今天天气怎么样？"
    }],
    tools=[{
        "type": "web_search",
        "max_keyword": 2
    }]
)
print(response)
```

---

## 5. 下一步建议

### 5.1 平台能力速览

- **提示词优化**: 学习如何编写更有效的提示词
- **权限管理**: 配置团队成员的访问权限
- **模型管理**: 管理您的模型部署和订阅

### 5.2 查看完整模型列表

在 [模型中心](https://console.volcengine.com/ark/region:ark+cn-beijing/model) 查看火山方舟支持的完整模型集。

### 5.3 深度学习更多功能

- [深度思考能力使用指南](https://www.volcengine.com/docs/82379/1956279)
- [多模态理解教程](https://www.volcengine.com/docs/82379/1362931)
- [批量推理 SDK 教程](https://www.volcengine.com/docs/82379/1399517)
- [函数调用 Function Calling](https://www.volcengine.com/docs/82379/1262342)

---

## 参考链接

- [官方文档首页](https://www.volcengine.com/docs/82379/1099455)
- [模型价格](https://www.volcengine.com/docs/82379/1544106)
- [API 参考](https://www.volcengine.com/docs/82379/1399008)

---

## 本项目集成说明

本项目 (Banana Slides) 已集成火山引擎方舟 API，您可以通过以下步骤使用：

### 1. 配置环境变量

在 `.env` 文件中设置：

```bash
# 切换到火山引擎提供商
AI_PROVIDER_FORMAT=volcengine

# 火山方舟 API Key
ARK_API_KEY=your-ark-api-key-here

# 文本模型（可选，默认使用豆包）
TEXT_MODEL=doubao-1-5-pro-32k-250115

# 图像生成模型（可选，默认使用 Seedream）
IMAGE_MODEL=doubao-seedream-3-0-t2i-250415
```

### 2. 安装依赖

```bash
pip install 'volcengine-python-sdk[ark]'
```

### 3. 在前端设置

也可以在前端设置页面选择"火山引擎"作为 AI 提供商格式。

### 4. 支持的模型

| 功能     | 推荐模型                           |
| -------- | ---------------------------------- |
| 文本生成 | `doubao-1-5-pro-32k-250115`        |
| 图像生成 | `doubao-seedream-3-0-t2i-250415`   |
| 图片理解 | `doubao-1-5-vision-pro-32k-250115` |

> **注意**: 请在 [火山方舟控制台](https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement) 开通相应模型服务后使用。