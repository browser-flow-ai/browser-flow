"""
RAG (Retrieval-Augmented Generation) 模块

职责：基于检索增强生成的问答系统
- 文档向量化：将文本转换为向量表示（支持 DashScope 和 TF-IDF 降级）
- 向量存储：使用 FAISS 存储和管理文档向量
- 语义检索：根据问题检索最相关的文档片段
- 答案生成：结合检索内容和 LLM 生成准确答案
- 配置管理：支持灵活的配置参数和环境变量

主要组件：
- rag_engine: RAG 问答引擎
- embeddings_manager: 嵌入向量管理器
- RAGConfig: 配置管理类
- PromptBuilder: 提示词构建器

支持的嵌入方案：
1. DashScope Embeddings（推荐）：高质量中文语义理解
2. SimpleEmbeddings（降级）：本地 TF-IDF 风格向量化
"""

from .rag_engine import (
    answer_question_with_rag,
    answer_question_with_rag_advanced,
    RAGConfig,
    PromptBuilder
)
from .embeddings_manager import (
    EmbeddingsManager,
    DashScopeEmbeddings,
    SimpleEmbeddings
)

__all__ = [
    'answer_question_with_rag',
    'answer_question_with_rag_advanced',
    'RAGConfig',
    'PromptBuilder',
    'EmbeddingsManager',
    'DashScopeEmbeddings',
    'SimpleEmbeddings'
]

__version__ = "1.0.0"
__description__ = "RAG (Retrieval-Augmented Generation) module for question answering"
