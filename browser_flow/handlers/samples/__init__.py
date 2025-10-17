"""
云南招聘信息智能问答系统

基于 RAG 技术和大语言模型的智能问答系统，可以自动从招聘公告网页中提取信息、
下载并解析附件，然后回答用户的问题。

主要功能：
- 自动提取网页内容和附件下载链接
- 支持多种文件格式解析（Excel、PDF、Word、WPS、RTF、HTML、XML、JSON、YAML、CSV、TXT）
- 基于 DashScope Embeddings 的高质量语义检索
- 支持 RAG 问答模式
- 智能嵌入方案选择（DashScope + SimpleEmbeddings 降级）
"""

__version__ = "2.0.0"
__author__ = "Browser Flow AI Team"

from browser_flow.handlers.web_with_attachment.data_models import Attachment, JobPosting
from browser_flow.handlers.web_with_attachment.web_extractor import extract_job_posting
from browser_flow.handlers.web_with_attachment.file_processor import download_and_parse_attachments
from browser_flow.handlers.rag.embeddings_manager import EmbeddingsManager, DashScopeEmbeddings, SimpleEmbeddings
from browser_flow.handlers.rag.rag_engine import answer_question_with_rag
from .workflow import process_url_rag

__all__ = [
    "Attachment",
    "JobPosting", 
    "extract_job_posting",
    "download_and_parse_attachments",
    "EmbeddingsManager",
    "DashScopeEmbeddings",
    "SimpleEmbeddings",
    "answer_question_with_rag",
    "process_url_rag",
]
