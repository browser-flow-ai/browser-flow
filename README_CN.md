# Browser-Flow

一个现代化的浏览器自动化集成工具套件，专为开发者和自动化爱好者设计。  
A modern browser automation integration toolkit designed specifically for developers and automation enthusiasts.

[中文版](README_CN.md) | [English](README.md)

## 项目简介

Browser-Flow 是一个模块化的浏览器自动化解决方案，将复杂的浏览器操作分解为多个独立且可组合的组件。每个组件都可以单独使用，也可以组合使用，为开发者提供灵活且强大的浏览器自动化能力。

## 核心组件

- **[browser-common](/browser-common)** - 基础依赖库，提供通用的浏览器操作接口
- **[browser-control](/browser-control)** - 基于大语言模型的智能浏览器操作引擎
- **[browser-flow](/browser-flow)** - 可定制的浏览器工作流编排系统
- **[browser-wrapper](/browser-wrapper)** - 在保证浏览器能正常稳定工作的情况下，获取A11y Tree时的浏览器封装层

## 快速开始

### 环境要求

- Python 3.13+
- Poetry（包管理器）

### 环境变量配置

目前支持 DeepSeek 和 Qwen 大模型，请设置以下环境变量：

```bash
# DeepSeek API 密钥
export DEEPSEEK_API_KEY="your_deepseek_api_key"

# Qwen API 密钥  
export AGENTQL_API_KEY="your_qwen_api_key"
```

或者在 `.env` 文件中配置：

```bash
DEEPSEEK_API_KEY="your_deepseek_api_key"
AGENTQL_API_KEY="your_qwen_api_key"
```

### 安装步骤

1. **检查Python环境**
   ```bash
   poetry env list
   poetry env use 3.13
   poetry run python --version
   ```

2. **安装依赖**
   ```bash
   poetry install
   poetry run playwright install chromium
   ```

3. **添加新包**（如需要）
   ```bash
   poetry add pydantic-ai
   ```

## 使用方法

Browser-Flow 提供了简单易用的封装类，让您能够快速开始浏览器自动化任务。

### 基本用法

#### 方式1：使用 BrowserFlow 类

```python
import asyncio
from browser_flow import BrowserFlow

async def main():
    # 创建 BrowserFlow 实例
    flow = BrowserFlow()
    
    try:
        # 执行浏览器自动化任务
        result = await flow.run("打开百度，然后关闭百度", max_steps=5)
        print(f"执行结果: {result}")
    except Exception as e:
        print(f"执行出错: {e}")
    finally:
        # 手动清理资源
        await flow.close()

# 运行示例
asyncio.run(main())
```

#### 方式2：使用便捷函数（推荐）

```python
import asyncio
from browser_flow import run_workflow

async def main():
    try:
        # 使用便捷函数，自动管理资源
        result = await run_workflow(
            "打开 https://books.toscrape.com/ 并提取书籍价格信息", 
            max_steps=10
        )
        print(f"执行结果: {result}")
    except Exception as e:
        print(f"执行出错: {e}")

# 运行示例
asyncio.run(main())
```

### 参数说明

- `instruction`: 浏览器自动化指令（字符串）
- `max_steps`: 最大执行步数（默认：10）
- `session_id`: 可选的会话ID（自动生成）

### 更多示例

查看 [browser_flow/example.py](browser_flow/example.py) 文件获取更多使用示例。

### 高级用法：直接使用 browser-control

如果您需要更精细的控制，可以直接使用 `browser-control` 模块：

```python
import asyncio
from browser_control.agent_hand import AgentHand
from pydantic import BaseModel, Field

# 定义数据提取模式
class BookSchema(BaseModel):
    """书籍信息模式"""
    title: str = Field(description="书籍标题")
    price: str = Field(description="书籍价格")
    rating: str = Field(description="书籍评分")

async def advanced_example():
    """高级用法示例"""
    # 创建 AgentHand 实例
    agent = AgentHand("advanced_example")
    
    try:
        await agent.init()
        
        # 1. 导航到网页
        await agent.goto("https://books.toscrape.com/")
        
        # 2. 观察页面元素
        elements = await agent.observe("查找书籍标题和价格")
        print(f"找到 {len(elements)} 个元素")
        
        # 3. 提取信息（文本方式）
        result = await agent.extract("提取所有书籍的名称、价格和评分")
        print(f"提取结果: {result}")
        
        # 4. 提取信息（结构化模式）
        structured_result = await agent.extract({
            "instruction": "提取书籍信息",
            "output_schema": BookSchema
        })
        print(f"结构化提取结果: {structured_result}")
        
        # 5. 执行操作
        await agent.act("点击第一本书")
        
        # 6. 提取详细信息
        details = await agent.extract("提取书籍详细信息")
        print(f"详细信息: {details}")
        
    except Exception as e:
        print(f"执行出错: {e}")
    finally:
        await agent.close()

# 运行示例
asyncio.run(advanced_example())
```

### browser-control 核心方法

- **`goto(url)`**: 导航到指定URL
- **`observe(instruction)`**: 观察页面元素，返回可操作元素列表
- **`extract(instruction)`**: 提取页面信息
- **`extract(schema_dict)`**: 使用结构化模式提取信息
- **`act(instruction)`**: 执行浏览器操作（点击、输入、按键等）

## 特性亮点

- 🚀 **模块化设计** - 每个组件独立运行，按需使用
- 🤖 **AI驱动** - 集成大语言模型，实现智能浏览器操作
- 🔧 **高度可定制** - 支持自定义工作流和操作逻辑
- 📱 **无障碍支持** - 内置A11y Tree支持，提升可访问性
- 🛡️ **稳定可靠** - 基于成熟的Playwright框架构建

## 技术说明

> **重要提示**：本项目借鉴了Stagehand的许多优秀设计，但针对Python版本与TypeScript版本之间的差异进行了深度优化，解决了原版本中存在的兼容性问题。

## 贡献指南

我们欢迎所有形式的贡献！如果您想为项目添砖加瓦，请：

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

如有问题或建议，请通过以下方式联系我们：

- 提交 [Issue](../../issues)
- 发起 [Discussion](../../discussions)

---

**Browser-Flow** - 让浏览器自动化变得简单而强大！