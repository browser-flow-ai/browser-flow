# Browser-Flow

一个现代化的浏览器自动化集成工具套件，专为开发者和自动化爱好者设计。

[中文版](README_CN.md) | [English](README.md)

## 项目简介

Browser-Flow 是一个模块化的浏览器自动化解决方案，将复杂的浏览器操作分解为多个独立且可组合的组件。每个组件都可以单独使用，也可以组合使用，为开发者提供灵活且强大的浏览器自动化能力。

## 核心组件

- **[browser-common](/browser-common)** - 基础依赖库，提供通用的浏览器操作接口
- **[browser-control](/browser-control)** - 基于大语言模型的智能浏览器操作引擎
- **[browser-flow](/browser-flow)** - 可定制的浏览器工作流编排系统
- **[browser-wrapper](/browser-wrapper)** - 获取A11y Tree时的浏览器封装层

## 快速开始

### 环境要求

- Python 3.13+
- Poetry（包管理器）

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