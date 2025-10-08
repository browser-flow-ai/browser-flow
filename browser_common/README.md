# Browser Common

Browser Common is the core foundation module of the BeamSearch browser automation toolkit, providing unified logging management, LLM integration, and common utility functions.

### 📦 Module Overview

Browser Common provides foundational services for the entire browser automation ecosystem, including:

- 🎯 **Unified Logging Management** - Provides consistent logging interfaces and configuration
- 🤖 **LLM Integration** - Supports multiple large language model services
- 🔧 **Common Utilities** - Shared utility functions and configuration management

### 🚀 Quick Start

#### Installation

```bash
# Install via Poetry (recommended)
poetry add browser_common

# Or install via pip
pip install browser_common
```

#### Basic Usage

```python
from browser_common import get_logger, llm_deepseek

# Create logger
logger = get_logger("my_module")
logger.info("Browser Common initialized successfully")

# Use LLM
response = llm_deepseek.llm.invoke("Hello, world!")
print(response.content)
```

### 📚 Core Features

#### 1. Logging Management System

Browser Common provides powerful logging management capabilities with support for multiple log formats and configuration methods.

##### Basic Logging

```python
from browser_common import get_logger

# Create logger
logger = get_logger("browser_control")

# Log different levels
logger.debug("Debug information")
logger.info("Operation successful", user_id=123, action="login")
logger.warning("Warning message", retry_count=3)
logger.error("Error occurred", error_code="TIMEOUT")
```

##### Advanced Logging Configuration

```python
from browser_common import BrowserCommonLogger, setup_logging

# Custom logger
logger = BrowserCommonLogger(
    module_name="custom_module",
    level="DEBUG",
    log_dir="custom_logs",
    enable_json_logging=True,
    session_id="session_001"
)

# Global logging configuration
setup_logging(
    level="INFO",
    log_dir="logs",
    enable_file_logging=True,
    enable_console_logging=True
)
```

##### Execution Time Monitoring

```python
logger = get_logger("performance")

# Use context manager to log execution time
with logger.log_execution_time("Page loading", url="https://example.com"):
    # Execute page loading operation
    load_page()
```

#### 2. LLM Integration

Browser Common integrates multiple large language model services, supporting DeepSeek and Qwen.

##### DeepSeek Integration

```python
from browser_common import llm_deepseek

# Use DeepSeek LLM
response = llm_deepseek.llm.invoke("Please help me analyze this webpage content")
print(response.content)

# Streaming response
for chunk in llm_deepseek.llm.stream("Please generate a webpage summary"):
    print(chunk.content, end="")
```

##### Qwen Integration

```python
from browser_common import llm_qwen

# Use Qwen LLM
response = llm_qwen.llm.invoke("Please help me extract key information from the webpage")
print(response.content)
```

##### Environment Configuration

```bash
# Set DeepSeek API Key
export DEEPSEEK_API_KEY="your_deepseek_api_key"

# Set Qwen API Key
export DASHSCOPE_API_KEY="your_dashscope_api_key"
```

### 🔧 API Reference

#### Logging Management API

##### BrowserCommonLogger

Main logger manager class.

**Constructor Parameters:**
- `module_name` (str): Module name
- `level` (str): Log level, default "INFO"
- `log_dir` (str): Log file directory, default "logs"
- `enable_file_logging` (bool): Enable file logging, default True
- `enable_console_logging` (bool): Enable console logging, default True
- `enable_json_logging` (bool): Enable JSON format logging, default False
- `session_id` (str, optional): Session ID

**Main Methods:**
- `debug(message, **context)`: Log debug message
- `info(message, **context)`: Log info message
- `warning(message, **context)`: Log warning message
- `error(message, **context)`: Log error message
- `critical(message, **context)`: Log critical message
- `log_execution_time(operation, **context)`: Execution time context manager

##### Utility Functions

- `get_logger(module_name, **kwargs)`: Create logger
- `get_cached_logger(module_name, **kwargs)`: Get cached logger
- `setup_logging(**kwargs)`: Set global logging configuration
- `setup_logging_from_config(config_path)`: Set logging from config file

#### LLM API

##### DeepSeek LLM

```python
from browser_common import llm_deepseek

# Basic invocation
response = llm_deepseek.llm.invoke("Your question")

# Streaming invocation
for chunk in llm_deepseek.llm.stream("Your question"):
    print(chunk.content, end="")

# Batch invocation
responses = llm_deepseek.llm.batch(["Question 1", "Question 2", "Question 3"])
```

##### Qwen LLM

```python
from browser_common import llm_qwen

# Basic invocation
response = llm_qwen.llm.invoke("Your question")

# Streaming invocation
for chunk in llm_qwen.llm.stream("Your question"):
    print(chunk.content, end="")
```

### 📁 Project Structure

```
browser_common/
├── __init__.py              # Package initialization
├── README.md                # Project documentation
├── browser_logging/         # Logging management module
│   ├── __init__.py
│   ├── logging_manager.py   # Core logging manager
│   ├── logging_config.py    # Logging configuration
│   ├── logging.yaml         # Default configuration file
│   └── README.md            # Detailed logging module docs
└── llm/                     # LLM integration module
    ├── __init__.py
    ├── llm_deepseek.py      # DeepSeek LLM configuration
    └── llm_qwen.py          # Qwen LLM configuration
```

### ⚙️ Configuration Options

#### Environment Variables

- `BROWSER_COMMON_LOG_LEVEL`: Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `DEEPSEEK_API_KEY`: DeepSeek API key
- `DASHSCOPE_API_KEY`: Qwen API key

#### Logging Configuration File

Supports YAML format logging configuration:

```yaml
# logging.yaml
version: 1
formatters:
  standard:
    format: '%(asctime)s | %(name)s | %(levelname)-8s | %(message)s'
handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
  file:
    class: logging.handlers.RotatingFileHandler
    filename: logs/browser_common.log
    maxBytes: 10485760
    backupCount: 5
    level: DEBUG
    formatter: standard
loggers:
  browser_common:
    level: INFO
    handlers: [console, file]
    propagate: false
```

### 🎯 Use Cases

#### 1. Browser Automation Projects

```python
from browser_common import get_logger, llm_deepseek

logger = get_logger("browser_automation")

async def automate_browser():
    logger.info("Starting browser automation task")
    
    # Use LLM to analyze page content
    analysis = llm_deepseek.llm.invoke("Analyze the current page structure")
    logger.info("Page analysis completed", analysis_length=len(analysis.content))
    
    # Log operation results
    logger.info("Automation task completed", success=True)
```

#### 2. Data Extraction Projects

```python
from browser_common import get_logger, llm_qwen

logger = get_logger("data_extraction")

def extract_data(url):
    with logger.log_execution_time("Data extraction", url=url):
        # Extract data
        data = extract_from_page(url)
        
        # Use LLM to clean data
        cleaned_data = llm_qwen.llm.invoke(f"Clean the following data: {data}")
        
        logger.info("Data extraction completed", 
                   url=url, 
                   data_size=len(data),
                   cleaned_size=len(cleaned_data.content))
        
        return cleaned_data.content
```

#### 3. Multi-Module Collaboration

```python
# Different modules using the same session_id
control_logger = get_logger("browser_control", session_id="session_001")
utils_logger = get_logger("browser_common", session_id="session_001")
flow_logger = get_logger("browser_flow", session_id="session_001")

control_logger.info("Starting navigation", url="https://example.com")
utils_logger.info("Page loading completed", load_time="2.1s")
flow_logger.info("Workflow execution completed", steps_completed=5)
```

### 🧪 Testing

Run test cases:

```bash
# Run all tests
pytest test/

# Run specific module tests
pytest test/test_logging.py
pytest test/test_llm.py
```

### 📈 Performance Optimization

#### Logging Performance Optimization

```python
# Use cached logger
logger = get_cached_logger("performance_critical_module")

# Batch log records
logger.info("Batch operations", operations=["op1", "op2", "op3"])

# Async logging (if supported)
await logger.async_info("Async operation completed")
```

#### LLM Performance Optimization

```python
# Batch LLM calls
questions = ["Question 1", "Question 2", "Question 3"]
responses = llm_deepseek.llm.batch(questions)

# Stream processing for large text
for chunk in llm_deepseek.llm.stream("Large text processing"):
    process_chunk(chunk.content)
```

### 🔒 Best Practices

#### 1. Logging Best Practices

```python
# ✅ Good practice
logger.info("User login successful", 
           user_id=123, 
           login_method="oauth",
           ip_address="192.168.1.1",
           session_duration="30m")

# ❌ Avoid
logger.info("Login successful")
```

#### 2. LLM Usage Best Practices

```python
# ✅ Good practice - Provide context
context = "This is an e-commerce product page"
prompt = f"Based on the following context, analyze the page content: {context}"
response = llm_deepseek.llm.invoke(prompt)

# ❌ Avoid - Lack of context
response = llm_deepseek.llm.invoke("Analyze page")
```

#### 3. Error Handling Best Practices

```python
try:
    result = perform_operation()
    logger.info("Operation successful", result_size=len(result))
except Exception as e:
    logger.error("Operation failed", 
                operation="data_extraction",
                error=str(e),
                error_type=type(e).__name__,
                retry_count=3)
    raise
```

### 🤝 Contributing

We welcome all forms of contributions! If you'd like to contribute to Browser Common:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

#### Development Environment Setup

```bash
# Clone repository
git clone https://github.com/your-org/beamsearch.git
cd beamsearch/browser_common

# Install development dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Code formatting
poetry run ruff format .
```

### 📄 License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.

### 📞 Support & Contact

If you have any questions or suggestions, please contact us through:

- Submit an [Issue](../../issues)
- Start a [Discussion](../../discussions)
- Send email to: y.champoo@gmail.com

---

**Browser Common** - Providing solid foundation services for browser automation!