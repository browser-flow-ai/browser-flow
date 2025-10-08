# Browser-Flow

A modern browser automation integration toolkit designed for developers and automation enthusiasts.

[中文版](README_CN.md) | [English](README.md)

## Project Overview

Browser-Flow is a modular browser automation solution that breaks down complex browser operations into multiple independent and composable components. Each component can be used standalone or in combination, providing developers with flexible and powerful browser automation capabilities.

## Core Components

- **[browser-common](browser-common)** - Core dependency library providing common browser operation interfaces
- **[browser-control](/browser-control)** - LLM-powered intelligent browser operation engine
- **[browser-flow](/browser-flow)** - Customizable browser workflow orchestration system
- **[browser-wrapper](/browser-wrapper)** - Browser wrapper layer for A11y Tree access

## Quick Start

### Prerequisites

- Python 3.13+
- Poetry (package manager)

### Installation Steps

1. **Check Python Environment**
   ```bash
   poetry env list
   poetry env use 3.13
   poetry run python --version
   ```

2. **Install Dependencies**
   ```bash
   poetry install
   poetry run playwright install chromium
   ```

3. **Add New Packages** (if needed)
   ```bash
   poetry add pydantic-ai
   ```

## Key Features

- 🚀 **Modular Design** - Each component runs independently, use as needed
- 🤖 **AI-Powered** - Integrated with large language models for intelligent browser operations
- 🔧 **Highly Customizable** - Support for custom workflows and operation logic
- 📱 **Accessibility Support** - Built-in A11y Tree support for enhanced accessibility
- 🛡️ **Stable & Reliable** - Built on the mature Playwright framework

## Technical Notes

> **Important**: This project draws inspiration from many excellent designs in Stagehand, but has been deeply optimized to address compatibility issues between the Python and TypeScript versions, resolving problems that existed in the original implementation.

## Contributing

We welcome all forms of contributions! If you'd like to contribute to the project:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

If you have questions or suggestions, please contact us through:

- Submit an [Issue](../../issues)
- Start a [Discussion](../../discussions)

---

**Browser-Flow** - Making browser automation simple and powerful!
