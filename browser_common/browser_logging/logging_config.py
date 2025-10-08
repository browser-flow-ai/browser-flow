"""Logging configuration utilities"""

import os
import logging.config
from pathlib import Path
from typing import Optional, Dict, Any


class LoggingConfig:
    """Logging configuration manager"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize logging configuration manager
        
        Args:
            config_dir: Configuration file directory, defaults to current file directory
        """
        if config_dir is None:
            config_dir = Path(__file__).parent
        
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "logging.yaml"
    
    def setup_logging(self, 
                     config_file: Optional[str] = None,
                     level: Optional[str] = None,
                     log_dir: str = "logs") -> bool:
        """
        Setup logging configuration
        
        Args:
            config_file: Configuration file path
            level: Log level override
            log_dir: Log directory
            
        Returns:
            Whether setup was successful
        """
        try:
            # Create log directory
            Path(log_dir).mkdir(parents=True, exist_ok=True)
            
            # Use specified config file or default config file
            config_path = config_file or self.config_file
            
            if config_path and os.path.exists(config_path):
                # Load configuration from YAML file
                import yaml
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                # Update log file paths
                self._update_log_paths(config, log_dir)
                
                # Apply level override
                if level:
                    self._override_log_level(config, level)
                
                logging.config.dictConfig(config)
                return True
            else:
                # Use basic configuration
                self._setup_basic_logging(level, log_dir)
                return True
                
        except Exception as e:
            print(f"Failed to setup logging configuration: {e}")
            # Fallback to basic configuration
            self._setup_basic_logging(level, log_dir)
            return False
    
    def _update_log_paths(self, config: Dict[str, Any], log_dir: str):
        """Update log file paths in configuration"""
        if 'handlers' in config:
            for handler_name, handler_config in config['handlers'].items():
                if 'filename' in handler_config:
                    # Update log file paths
                    filename = handler_config['filename']
                    if not os.path.isabs(filename):
                        handler_config['filename'] = os.path.join(log_dir, filename)
    
    def _override_log_level(self, config: Dict[str, Any], level: str):
        """Override log level in configuration"""
        if 'loggers' in config:
            for logger_name, logger_config in config['loggers'].items():
                logger_config['level'] = level.upper()
        
        if 'root' in config:
            config['root']['level'] = level.upper()
    
    def _setup_basic_logging(self, level: Optional[str], log_dir: str):
        """Setup basic logging configuration"""
        log_level = getattr(logging, (level or "INFO").upper())
        
        # Create log directory
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # Basic configuration
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s | %(name)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(
                    os.path.join(log_dir, 'browser_common.log'),
                    encoding='utf-8'
                )
            ]
        )
    
    def get_logger_config(self, module_name: str) -> Dict[str, Any]:
        """
        Get logging configuration for specified module
        
        Args:
            module_name: Module name
            
        Returns:
            Logging configuration dictionary
        """
        return {
            'level': os.getenv('BROWSER_COMMON_LOG_LEVEL', 'INFO'),
            'format': '%(asctime)s | %(name)s | %(levelname)-8s | %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'handlers': ['console', 'file']
        }


# Global configuration instance
_config_manager = LoggingConfig()


def setup_logging(**kwargs) -> bool:
    """
    Quick setup logging configuration
    
    Args:
        **kwargs: Parameters passed to LoggingConfig.setup_logging
        
    Returns:
        Whether setup was successful
    """
    return _config_manager.setup_logging(**kwargs)


def get_config() -> LoggingConfig:
    """
    Get configuration manager instance
    
    Returns:
        LoggingConfig instance
    """
    return _config_manager
