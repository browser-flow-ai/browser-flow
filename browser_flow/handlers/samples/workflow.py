"""
RAG 工作流程编排
"""

import logging
import os
from browser_flow.handlers.web_with_attachment.web_extractor import extract_job_posting
from browser_flow.handlers.web_with_attachment.file_processor import download_and_parse_attachments
from browser_flow.handlers.rag.rag_engine import answer_question_with_rag, answer_question_with_rag_advanced

logger = logging.getLogger(__name__)


async def process_url_rag(base_url: str, url: str, question: str) -> str:
    """
    使用 RAG 模式处理URL和问题
    
    Args:
        base_url: 基础URL
        url: 招聘公告URL
        question: 用户问题
        
    Returns:
        str: 生成的答案
    """
    # 提取招聘公告信息
    job_posting = await extract_job_posting(base_url, url)
    
    # 设置下载目录
    downloads_dir = os.path.join(os.path.dirname(__file__), "downloads")
    
    try:
        logger.info('=== 开始下载和解析附件 ===\n')
        
        # 下载并解析所有附件
        attachments_content = await download_and_parse_attachments(
            job_posting.attachments,
            downloads_dir
        )
        
        logger.info('\n=== 附件处理完成 ===')
        logger.debug(f'总附件内容长度: {len(attachments_content)} 字符')
        
        # 选择使用哪种 RAG 方法
        use_advanced = os.getenv('USE_ADVANCED_RAG', 'false').lower() == 'true'
        
        if use_advanced:
            print('\n📊 使用高级 RAG (带 MMR 重排序)')
            # 使用高级 RAG（带 MMR 重排序）
            from browser_flow.handlers.rag.rag_engine import RAGConfig
            config = RAGConfig(
                chunk_size=1000,
                chunk_overlap=200,
                top_k=15,
                search_type="mmr"
            )
            answer = await answer_question_with_rag_advanced(
                job_posting,
                attachments_content,
                question,
                config=config,
                prompt_type="recruitment"
            )
        else:
            print('\n🔍 使用标准 RAG (语义检索)')
            # 使用标准 RAG
            answer = await answer_question_with_rag(
                job_posting, 
                attachments_content, 
                question,
                prompt_type="recruitment"
            )
        
        logger.debug('\n\n========================================')
        logger.debug('=== 最终答案 ===')
        logger.debug('========================================\n')
        logger.debug(answer)
        logger.debug('\n========================================\n')
        
        return answer
    except Exception as error:
        logger.error('程序执行出错:', error)
        raise error
