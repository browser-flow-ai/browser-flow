# Browser Common 日志管理系统

这是一个为 browser-common 包设计的统一日志管理系统，提供了灵活的日志记录、配置和管理功能。

## 功能特性

- 🎯 **统一接口**: 提供一致的日志记录接口
- 📝 **多种格式**: 支持文本和JSON格式日志
- ⚙️ **灵活配置**: 支持代码配置和YAML配置文件
- 🚀 **性能优化**: 支持日志器缓存和异步记录
- 📊 **上下文支持**: 支持结构化上下文信息
- ⏱️ **执行时间**: 内置执行时间记录功能
- 🔄 **日志轮转**: 自动日志文件轮转和压缩

## 快速开始

### 基本使用

```python
from browser_common import get_logger

# 创建日志器
logger = get_logger("my_module")

# 记录日志
logger.info("这是一条信息日志")
logger.error("这是一条错误日志")

# 带上下文的日志
logger.info("用户操作", user_id=123, action="login", ip="192.168.1.1")
```

### 高级使用

```python
from browser_common import get_logger, setup_logging

# 设置日志配置
setup_logging(level="DEBUG", log_dir="logs")

# 创建带会话ID的日志器
logger = get_logger("browser_control", session_id="session_001")

# 使用执行时间上下文管理器
with logger.log_execution_time("页面截图", page="example.com"):
    # 执行操作
    take_screenshot()

# JSON格式日志
json_logger = get_logger("api_client", enable_json_logging=True)
json_logger.info("API调用", 
                endpoint="/api/users", 
                method="GET", 
                status_code=200,
                response_time="0.5s")
```

## 配置选项

### 环境变量

- `BROWSER_COMMON_LOG_LEVEL`: 设置日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### 代码配置

```python
from browser_common import BrowserCommonLogger

logger = BrowserCommonLogger(
    module_name="my_module",
    level="INFO",
    log_dir="logs",
    enable_file_logging=True,
    enable_console_logging=True,
    enable_json_logging=False,
    session_id="session_001"
)
```

### YAML配置文件

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

## API 参考

### BrowserCommonLogger

主要的日志管理器类。

#### 构造函数参数

- `module_name` (str): 模块名称
- `level` (str): 日志级别，默认 "INFO"
- `log_dir` (str): 日志文件目录，默认 "logs"
- `enable_file_logging` (bool): 是否启用文件日志，默认 True
- `enable_console_logging` (bool): 是否启用控制台日志，默认 True
- `enable_json_logging` (bool): 是否启用JSON格式日志，默认 False
- `session_id` (str, optional): 会话ID

#### 主要方法

- `debug(message, **context)`: 记录调试日志
- `info(message, **context)`: 记录信息日志
- `warning(message, **context)`: 记录警告日志
- `error(message, **context)`: 记录错误日志
- `critical(message, **context)`: 记录严重错误日志
- `log_execution_time(operation, **context)`: 执行时间上下文管理器

### 工具函数

- `get_logger(module_name, **kwargs)`: 创建日志器
- `get_cached_logger(module_name, **kwargs)`: 获取缓存的日志器
- `setup_logging(**kwargs)`: 设置全局日志配置

## 使用示例

### 1. 基本日志记录

```python
from browser_common import get_logger

logger = get_logger("browser_control")
logger.info("浏览器启动成功", version="1.0.0")
logger.error("页面加载失败", url="https://example.com", error="timeout")
```

### 2. 结构化日志

```python
logger = get_logger("form_handler")
logger.info("表单提交", 
           form_id="login_form",
           fields=["username", "password"],
           validation_passed=True)
```

### 3. 执行时间监控

```python
logger = get_logger("performance")

with logger.log_execution_time("页面加载", url="https://example.com"):
    # 执行页面加载操作
    load_page()
```

### 4. 多模块协作

```python
# 不同模块使用相同的session_id
control_logger = get_logger("browser_control", session_id="session_001")
utils_logger = get_logger("browser_common", session_id="session_001")

control_logger.info("开始导航", url="https://example.com")
utils_logger.info("页面加载完成", load_time="2.1s")
```

### 5. JSON格式日志

```python
json_logger = get_logger("api_client", enable_json_logging=True)
json_logger.info("API响应", 
                endpoint="/api/data",
                status_code=200,
                response_size="1.2MB",
                processing_time="0.3s")
```

## 最佳实践

### 1. 模块命名

使用清晰的模块命名约定：

```python
# 好的命名
logger = get_logger("browser_control.navigation")
logger = get_logger("browser_common.element_finder")
logger = get_logger("browser_wrapper.chrome")

# 避免的命名
logger = get_logger("logger")
logger = get_logger("test")
```

### 2. 上下文信息

提供有意义的上下文信息：

```python
# 好的上下文
logger.info("元素点击", 
           selector="button.submit",
           element_type="button",
           clickable=True,
           page_url="https://example.com")

# 避免的上下文
logger.info("点击", element="button")
```

### 3. 错误处理

在异常处理中记录详细信息：

```python
try:
    # 执行操作
    perform_action()
except Exception as e:
    logger.error("操作失败", 
                operation="form_submit",
                error=str(e),
                error_type=type(e).__name__,
                retry_count=3)
```

### 4. 性能监控

使用执行时间上下文管理器监控性能：

```python
with logger.log_execution_time("数据库查询", table="users", query_type="select"):
    result = database.query("SELECT * FROM users")
```

## 测试

运行测试用例：

```bash
python test_logging.py
```

运行使用示例：

```bash
python examples.py
```

## 文件结构

```
src/
├── __init__.py              # 包初始化文件
├── logging_manager.py       # 核心日志管理器
├── logging_config.py        # 日志配置管理
├── logging.yaml            # 默认配置文件
├── examples.py             # 使用示例
└── test_logging.py         # 测试用例
```

## 许可证

MIT License
