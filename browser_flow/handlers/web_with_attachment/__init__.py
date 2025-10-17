"""
Web with Attachment 模块

职责：网页内容提取和文件下载处理
- 网页内容提取：使用 AgentHand 提取网页标题、正文和附件链接
- 文件下载：下载网页中的附件文件
- 文件解析：解析多种格式的文件（Excel、PDF、Word、WPS、RTF、HTML、XML、JSON、YAML等）
- 内容缓存：基于文件名检查已下载内容，避免重复下载

主要组件：
- web_extractor: 网页内容提取
- file_processor: 文件下载和解析
- data_models: 数据结构定义
"""

from .web_extractor import extract_job_posting
from .file_processor import download_and_parse_attachments, process_single_file
from .data_models import JobPosting, Attachment

__all__ = [
    'extract_job_posting',
    'download_and_parse_attachments', 
    'process_single_file',
    'JobPosting',
    'Attachment'
]

__version__ = "1.0.0"
__description__ = "Web content extraction and file processing module"
