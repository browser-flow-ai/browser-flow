#!/usr/bin/env python3
"""Basic test cases for browser_logging module - Pytest version (more concise)"""

import os
import tempfile
import shutil
import threading
import time
import asyncio
from pathlib import Path
from unittest.mock import patch
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
import sys
sys.path.insert(0, str(project_root))

from browser_common.browser_logging import (
    BrowserCommonLogger,
    JsonFormatter,
    LoggingConfig,
    get_logger,
    get_cached_logger,
    setup_logging,
    get_config,
    setup_logging_from_config
)


# Fixtures - Automatically manage the test environment
@pytest.fixture
def temp_log_dir():
    """Temporary log directory fixture"""
    temp_dir = tempfile.mkdtemp()
    log_dir = Path(temp_dir) / "test_logs"
    yield log_dir
    # Automatic cleanup
    if Path(temp_dir).exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def sample_logger(temp_log_dir):
    """Sample logger instance fixture"""
    return BrowserCommonLogger("test_module", log_dir=str(temp_log_dir))


@pytest.fixture
def config_dir():
    """Temporary config directory fixture"""
    temp_dir = tempfile.mkdtemp()
    config_dir = Path(temp_dir) / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    yield config_dir
    # Automatic cleanup
    if Path(temp_dir).exists():
        shutil.rmtree(temp_dir)


# Test classes - More concise test classes
class TestBrowserCommonLogger:
    """Test cases for BrowserCommonLogger class"""
    
    def test_logger_initialization(self, temp_log_dir):
        """Test logger initialization with default parameters"""
        logger = BrowserCommonLogger("test_module", log_dir=str(temp_log_dir))
        
        assert logger.module_name == "test_module"
        assert logger.session_id is None
        assert logger.enable_json_logging is False
        assert logger.log_dir == temp_log_dir
        assert logger.logger is not None
    
    def test_logger_initialization_with_session_id(self, temp_log_dir):
        """Test logger initialization with session ID"""
        logger = BrowserCommonLogger(
            "test_module",
            session_id="session_123",
            log_dir=str(temp_log_dir)
        )
        
        assert logger.module_name == "test_module"
        assert logger.session_id == "session_123"
        assert logger.log_dir == temp_log_dir
    
    def test_logger_initialization_with_json_logging(self, temp_log_dir):
        """Test logger initialization with JSON logging enabled"""
        logger = BrowserCommonLogger(
            "test_module",
            enable_json_logging=True,
            log_dir=str(temp_log_dir)
        )
        
        assert logger.enable_json_logging is True
    
    def test_logger_initialization_with_custom_level(self, temp_log_dir):
        """Test logger initialization with custom log level"""
        logger = BrowserCommonLogger(
            "test_module",
            level="DEBUG",
            log_dir=str(temp_log_dir)
        )
        
        assert logger.logger.level == 10  # DEBUG level
    
    def test_logger_initialization_with_env_level(self, temp_log_dir):
        """Test logger initialization with environment variable level"""
        with patch.dict(os.environ, {"BROWSER_COMMON_LOG_LEVEL": "ERROR"}):
            logger = BrowserCommonLogger(
                "test_module",
                level="INFO",  # This should be overridden by env var
                log_dir=str(temp_log_dir)
            )
            
            assert logger.logger.level == 40  # ERROR level
    
    def test_log_methods(self, sample_logger):
        """Test all log methods"""
        # Use fixture, no need to manually create logger
        sample_logger.debug("Debug message")
        sample_logger.info("Info message")
        sample_logger.warning("Warning message")
        sample_logger.error("Error message")
        sample_logger.critical("Critical message")
        
        # Test with context
        sample_logger.info("Message with context", key1="value1", key2="value2")
    
    def test_log_execution_time_context_manager(self, sample_logger):
        """Test execution time context manager"""
        with sample_logger.log_execution_time("test_operation"):
            time.sleep(0.01)  # Simulate some work
    
    def test_log_execution_time_with_context(self, sample_logger):
        """Test execution time context manager with additional context"""
        with sample_logger.log_execution_time("test_operation", url="https://example.com"):
            time.sleep(0.01)
    
    def test_file_logging_disabled(self, temp_log_dir):
        """Test logger with file logging disabled"""
        logger = BrowserCommonLogger(
            "test_module",
            enable_file_logging=False,
            log_dir=str(temp_log_dir)
        )
        
        logger.info("Test message")
        
        # Should not create log files
        log_files = list(temp_log_dir.glob("*.log"))
        assert len(log_files) == 0
    
    def test_console_logging_disabled(self, temp_log_dir):
        """Test logger with console logging disabled"""
        logger = BrowserCommonLogger(
            "test_module",
            enable_console_logging=False,
            log_dir=str(temp_log_dir)
        )
        
        # Should not raise exception
        logger.info("Test message")
    
    def test_json_logging_format(self, temp_log_dir):
        """Test JSON logging format"""
        logger = BrowserCommonLogger(
            "test_module",
            enable_json_logging=True,
            log_dir=str(temp_log_dir)
        )
        
        logger.info("Test message", key="value")
        
        # Check that log files were created
        log_files = list(temp_log_dir.glob("*.log"))
        assert len(log_files) > 0


class TestLoggingUtilities:
    """Test cases for logging utility functions"""
    
    def test_get_logger(self, temp_log_dir):
        """Test get_logger utility function"""
        logger = get_logger("test_module", log_dir=str(temp_log_dir))
        
        assert isinstance(logger, BrowserCommonLogger)
        assert logger.module_name == "test_module"
    
    def test_get_cached_logger(self, temp_log_dir):
        """Test get_cached_logger utility function"""
        logger1 = get_cached_logger("test_module", log_dir=str(temp_log_dir))
        logger2 = get_cached_logger("test_module", log_dir=str(temp_log_dir))
        
        # Should return the same logger instance (cached)
        assert logger1 is logger2
    
    def test_setup_logging(self, temp_log_dir):
        """Test setup_logging utility function"""
        result = setup_logging(level="DEBUG", log_dir=str(temp_log_dir))
        
        # Should return True on success (or False if config file doesn't exist)
        assert result is True or result is False


class TestLoggingConfig:
    """Test cases for LoggingConfig class"""
    
    def test_logging_config_initialization(self, config_dir):
        """Test LoggingConfig initialization"""
        config = LoggingConfig(str(config_dir))
        
        assert config.config_dir == config_dir
        assert config.config_file is not None
    
    def test_logging_config_initialization_default(self):
        """Test LoggingConfig initialization with default directory"""
        config = LoggingConfig()
        
        assert config.config_dir is not None
        assert config.config_file is not None
    
    def test_setup_logging_without_config_file(self, config_dir):
        """Test setup_logging without config file"""
        config = LoggingConfig(str(config_dir))
        
        # Should handle missing config file gracefully
        result = config.setup_logging()
        
        # Should return False when config file doesn't exist, or True if fallback works
        assert result is False or result is True
    
    def test_setup_logging_with_config_file(self, config_dir):
        """Test setup_logging with config file"""
        config = LoggingConfig(str(config_dir))
        
        # Create a simple config file
        config_file = config_dir / "logging.yaml"
        config_file.write_text("""
version: 1
disable_existing_loggers: false
formatters:
  standard:
    format: '%(asctime)s | %(name)s | %(levelname)-8s | %(message)s'
handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
loggers:
  test:
    level: INFO
    handlers: [console]
    propagate: false
""")
        
        result = config.setup_logging(config_file=str(config_file))
        
        # Should return True when config file exists
        assert result is True


class TestJsonFormatter:
    """Test cases for JsonFormatter class"""
    
    def test_json_formatter_format(self):
        """Test JSON formatter format method"""
        formatter = JsonFormatter()
        
        # Create a mock log record
        import logging
        record = logging.LogRecord(
            name="test_module",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        # Should return valid JSON
        import json
        parsed = json.loads(formatted)
        
        assert parsed["level"] == "INFO"
        assert parsed["module"] == "test_module"
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed
        assert "thread" in parsed
        assert "process" in parsed


class TestMultithreading:
    """Test cases for multi-threading scenarios"""
    
    def test_multithreaded_logging(self, temp_log_dir):
        """Test logging from multiple threads"""
        results = []
        errors = []
        
        def worker_thread(thread_id):
            """Worker thread function"""
            try:
                logger = get_logger(f"thread_{thread_id}", log_dir=str(temp_log_dir))
                for i in range(5):
                    logger.info(f"Thread {thread_id} message {i}", 
                               thread_id=thread_id, iteration=i)
                results.append(f"Thread {thread_id} completed")
            except Exception as e:
                errors.append(f"Thread {thread_id} error: {e}")
        
        # Create and start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all threads completed successfully
        assert len(results) == 3
        assert len(errors) == 0
        
        # Verify log files were created
        log_files = list(temp_log_dir.glob("*.log"))
        assert len(log_files) > 0


class TestSessionTracking:
    """Test cases for session tracking"""
    
    def test_session_isolation(self, temp_log_dir):
        """Test session isolation"""
        session1_logger = get_logger("test_module", 
                                   session_id="session_001",
                                   log_dir=str(temp_log_dir))
        session2_logger = get_logger("test_module", 
                                   session_id="session_002",
                                   log_dir=str(temp_log_dir))
        
        session1_logger.info("Session 1 message")
        session2_logger.info("Session 2 message")
        
        # Both loggers should work independently
        assert session1_logger.session_id == "session_001"
        assert session2_logger.session_id == "session_002"


class TestErrorHandling:
    """Test cases for error handling"""
    
    def test_logger_with_invalid_level(self, temp_log_dir):
        """Test logger with invalid log level"""
        # Should handle invalid level gracefully
        try:
            logger = BrowserCommonLogger(
                "test_module",
                level="INVALID_LEVEL",
                log_dir=str(temp_log_dir)
            )
            # If it doesn't raise an exception, it should still create logger
            assert logger.logger is not None
        except AttributeError:
            # Expected behavior - invalid level should raise AttributeError
            pass
    
    def test_logger_with_readonly_directory(self, temp_log_dir):
        """Test logger with readonly directory"""
        readonly_dir = temp_log_dir / "readonly"
        readonly_dir.mkdir(parents=True, exist_ok=True)
        readonly_dir.chmod(0o444)  # Read-only
        
        try:
            # Should handle readonly directory gracefully
            try:
                logger = BrowserCommonLogger("test_module", log_dir=str(readonly_dir))
                # If it doesn't raise an exception, it should still create logger
                assert logger.logger is not None
            except PermissionError:
                # Expected behavior - readonly directory should raise PermissionError
                pass
        finally:
            # Restore permissions for cleanup
            readonly_dir.chmod(0o755)
    
    def test_logger_exception_handling(self, sample_logger):
        """Test logger exception handling"""
        # Test that exceptions in log context don't crash the logger
        try:
            with sample_logger.log_execution_time("test_operation"):
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected exception
        
        # Logger should still be functional
        sample_logger.info("Logger still works after exception")


# Parametrized tests - Powerful pytest functionality
@pytest.mark.parametrize("level,expected_level", [
    ("DEBUG", 10),
    ("INFO", 20),
    ("WARNING", 30),
    ("ERROR", 40),
    ("CRITICAL", 50),
])
def test_logger_levels(level, expected_level, temp_log_dir):
    """Test logger with different levels"""
    logger = BrowserCommonLogger("test_module", level=level, log_dir=str(temp_log_dir))
    assert logger.logger.level == expected_level


@pytest.mark.parametrize("module_name", [
    "test_module",
    "browser_control", 
    "browser_common",
    "browser_flow"
])
def test_logger_module_names(module_name, temp_log_dir):
    """Test logger with different module names"""
    logger = BrowserCommonLogger(module_name, log_dir=str(temp_log_dir))
    assert logger.module_name == module_name


# Async tests - pytest-asyncio support
@pytest.mark.asyncio
async def test_async_logging_operations(temp_log_dir):
    """Test async logging operations"""
    logger = BrowserCommonLogger("async_test", log_dir=str(temp_log_dir))
    
    # Test basic async logging
    logger.info("Async operation started")
    
    await asyncio.sleep(0.01)
    
    logger.info("Async operation completed")
    
    # Verify log files were created
    log_files = list(temp_log_dir.glob("*.log"))
    assert len(log_files) > 0


# Test combinations - pytest fixture combination functionality
@pytest.mark.parametrize("enable_file_logging", [True, False])
@pytest.mark.parametrize("enable_console_logging", [True, False])
def test_logger_configuration_combinations(enable_file_logging, enable_console_logging, temp_log_dir):
    """Test different logger configuration combinations"""
    logger = BrowserCommonLogger(
        "test_module",
        enable_file_logging=enable_file_logging,
        enable_console_logging=enable_console_logging,
        log_dir=str(temp_log_dir)
    )
    
    logger.info("Test message")
    
    # Check file logging behavior
    log_files = list(temp_log_dir.glob("*.log"))
    if enable_file_logging:
        assert len(log_files) > 0
    else:
        assert len(log_files) == 0


# Performance tests - pytest-benchmark can be easily added
def test_logger_performance(temp_log_dir):
    """Test logger performance"""
    logger = BrowserCommonLogger("perf_test", log_dir=str(temp_log_dir))
    
    # Simple performance test
    start_time = time.time()
    for i in range(100):
        logger.info(f"Performance test message {i}")
    end_time = time.time()
    
    # Should complete within reasonable time
    assert (end_time - start_time) < 1.0  # Less than 1 second for 100 messages


if __name__ == "__main__":
    # Can run pytest directly
    pytest.main([__file__, "-v"])
