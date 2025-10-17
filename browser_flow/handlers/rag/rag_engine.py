"""
RAG 问答引擎

使用 RAG (Retrieval-Augmented Generation) 回答问题

RAG 流程:
1. 文档分块 - 将大文档分割成小块
2. 向量化 - 将文档块转换为向量 (embeddings)
3. 存储 - 将向量存储到向量数据库
4. 检索 - 根据问题语义检索最相关的文档块
5. 生成 - 将检索到的内容传递给 LLM 生成答案
"""

import logging
from typing import Optional, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.llms.base import LLM

from browser_flow.handlers.web_with_attachment.data_models import JobPosting
from browser_flow.handlers.rag.embeddings_manager import EmbeddingsManager, DashScopeEmbeddings
from browser_common.llm.llm_qwen import llm as llm_qwen

logger = logging.getLogger(__name__)


class RAGConfig:
    """RAG 配置类 - 避免硬编码"""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        top_k: int = 15,
        search_type: str = "similarity",
        batch_size: int = 25,
        delay_between_batches: float = 0.1
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k
        self.search_type = search_type
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches


class PromptBuilder:
    """提示词构建器 - 动态生成提示词"""
    
    @staticmethod
    def build_general_prompt() -> str:
        """构建通用提示词模板"""
        return """
你是一个专业的文档信息分析助手。请基于以下从文档中检索到的相关内容，回答用户的问题。

检索到的相关内容:
{context}

问题: {question}

【关键提示】：
1. 请仔细分析所有文档内容，自动识别相关信息
2. 区分主要信息和参考信息
3. 重点关注包含具体要求和详细信息的文件
4. 忽略无关的参考信息，只关注核心内容

请仔细分析所有文档内容，如果找到相关信息，请明确说明：
1. 是否包含相关信息
2. 具体是哪些内容
3. 相关要求和条件
4. 其他重要细节

【重要】如果有多个相关内容，请全部列出，不要遗漏任何一个。
如果没有找到相关信息，请明确说"没有找到相关信息"。

答案:
"""

    @staticmethod
    def build_recruitment_prompt() -> str:
        """构建招聘相关的提示词模板"""
        return """
你是一个专业的招聘信息分析助手。请基于以下从招聘公告中检索到的相关内容，回答用户的问题。

检索到的相关内容:
{context}

问题: {question}

【关键提示】：
1. 请仔细分析所有附件内容，自动识别哪些是本次招聘的实际岗位信息
2. 区分招聘岗位信息和其他参考信息（如专业目录、学科名单等）
3. 重点关注包含具体岗位要求、专业要求、招聘人数等信息的文件
4. 忽略其他学校或机构的参考信息，只关注本次招聘的实际岗位

【专业适配规则】：
- 艺术设计相关专业包括：环境设计、艺术、设计、艺术学、设计学、设计学类
- 相关专业代码：A1305、A130502、1357、1351
- 上述任何一个专业名称或代码都属于艺术设计适配范围

请仔细分析所有附件内容，自动识别招聘岗位信息，如果找到相关岗位，请明确说明：
1. 是否招收相关专业（或其适配专业）的人员
2. 具体是哪些岗位（**请列出所有相关岗位**，包括岗位编号、岗位名称）
3. 每个岗位的学历要求（是否接受应届毕业生）
4. 每个岗位的其他相关要求（如年龄、性别、专业代码等）

【重要】如果有多个岗位符合条件，请全部列出，不要遗漏任何一个。
【特别注意】如果有性别要求不同的相同岗位（如"男性"和"女性"），务必分别列出，不要合并或省略。
如果没有找到相关岗位，请明确说"没有找到相关岗位"。

答案:
"""




async def answer_question_with_rag(
    job_posting: JobPosting,
    attachments_content: str,
    question: str,
    llm: Optional[LLM] = None,
    config: Optional[RAGConfig] = None,
    prompt_type: str = "recruitment"
) -> str:
    """
    使用 RAG 回答问题
    
    Args:
        job_posting: 招聘公告信息
        attachments_content: 附件内容
        question: 用户问题
        llm: 语言模型，如果为None则使用默认的Qwen
        config: RAG配置，如果为None则使用默认配置
        prompt_type: 提示词类型 ("general" 或 "recruitment")
        
    Returns:
        str: 生成的答案
    """
    if config is None:
        config = RAGConfig()
    
    print("\n\n=== 开始使用 RAG 处理问题 ===")
    print(f"问题: {question}")

    # 1. 准备文档内容
    full_text = f"""
招聘公告标题: {job_posting.title}

招聘公告内容:
{job_posting.content}

附件内容:
{attachments_content}
"""

    print(f"\n总文本长度: {len(full_text)} 字符")

    # 2. 文档分块
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )

    chunks = text_splitter.split_text(full_text)
    print(f"文本被分割为 {len(chunks)} 个块")

    # 3. 创建文档对象
    documents = [
        Document(
            page_content=chunk,
            metadata={
                "chunk_index": index,
                "source": "招聘公告及附件",
            }
        )
        for index, chunk in enumerate(chunks)
    ]

    print("\n=== 初始化向量数据库 ===")
    
    # 4. 创建 Embeddings（智能选择最佳方案）
    embeddings_manager = EmbeddingsManager()
    embeddings = await embeddings_manager.get_embeddings()
    embeddings_type = embeddings_manager.get_embeddings_type()

    # 5. 创建向量存储并添加文档
    print(f"\n正在生成文档向量（使用 {embeddings_type}）...")
    
    if isinstance(embeddings, DashScopeEmbeddings):
        # 使用异步版本
        vectorstore = FAISS.from_documents(documents, embeddings)
    else:
        # 使用同步版本
        vectorstore = FAISS.from_documents(documents, embeddings)
        
    print(f"✓ 已将 {len(documents)} 个文档块向量化并存储")

    # 6. 创建检索器（语义搜索）
    print("\n=== 执行语义检索 ===")
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": config.top_k}
    )

    # 7. 检索相关文档
    relevant_docs = retriever.get_relevant_documents(question)
    print(f"✓ 找到 {len(relevant_docs)} 个相关文档块")
    
    # 打印每个文档块的相关度信息
    for index, doc in enumerate(relevant_docs):
        preview = doc.page_content[:100].replace("\n", " ")
        print(f"  {index + 1}. [块 {doc.metadata['chunk_index']}] {preview}...")

    # 8. 构建提示词模板
    if prompt_type == "recruitment":
        template = PromptBuilder.build_recruitment_prompt()
    else:
        template = PromptBuilder.build_general_prompt()
    
    prompt_template = PromptTemplate(
        input_variables=["context", "question"],
        template=template
    )

    # 9. 将检索到的文档组合成上下文
    context = "\n\n---\n\n".join(doc.page_content for doc in relevant_docs)

    # 10. 使用LLM生成答案
    if llm is None:
        llm = llm_qwen

    print("\n=== 调用 大模型生成答案 ===\n")
    
    # 创建问答链
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )
    
    # 直接使用prompt和LLM
    prompt = prompt_template.format(context=context, question=question)
    
    # 将字符串转换为消息对象
    from langchain.schema import HumanMessage
    messages = [HumanMessage(content=prompt)]
    result = llm.invoke(messages)
    
    return result.content if hasattr(result, 'content') else str(result)


async def answer_question_with_rag_advanced(
    job_posting: JobPosting,
    attachments_content: str,
    question: str,
    llm: Optional[LLM] = None,
    config: Optional[RAGConfig] = None,
    prompt_type: str = "recruitment"
) -> str:
    """
    使用 RAG 和重排序回答问题（高级版本）
    
    额外功能:
    - 使用 MMR (Maximal Marginal Relevance) 检索，避免重复内容
    - 可以配置更多参数
    
    Args:
        job_posting: 招聘公告信息
        attachments_content: 附件内容
        question: 用户问题
        llm: 语言模型
        config: RAG配置，如果为None则使用默认配置
        prompt_type: 提示词类型 ("general" 或 "recruitment")
        
    Returns:
        str: 生成的答案
    """
    if config is None:
        config = RAGConfig()
    
    print("\n\n=== 开始使用高级 RAG 处理问题 ===")
    print(f"问题: {question}")
    print(f"配置: 块大小={config.chunk_size}, 重叠={config.chunk_overlap}, Top-K={config.top_k}, 搜索类型={config.search_type}")

    # 准备文档内容
    full_text = f"""
招聘公告标题: {job_posting.title}

招聘公告内容:
{job_posting.content}

附件内容:
{attachments_content}
"""

    print(f"\n总文本长度: {len(full_text)} 字符")

    # 文档分块
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )

    chunks = text_splitter.split_text(full_text)
    print(f"文本被分割为 {len(chunks)} 个块")

    # 创建文档对象
    documents = [
        Document(
            page_content=chunk,
            metadata={
                "chunk_index": index,
                "source": "招聘公告及附件",
            }
        )
        for index, chunk in enumerate(chunks)
    ]

    print("\n=== 初始化向量数据库 ===")

    # 创建 Embeddings（优先使用DashScope，不可用时降级）
    embeddings = None
    embeddings_type = "unknown"
    
    # 方案1: 尝试使用 DashScope（最佳：阿里云通义千问，高质量中文支持）
    try:
        dashscope_embeddings = DashScopeEmbeddings()
        is_connected = await dashscope_embeddings.test_connection()
        if is_connected:
            embeddings = dashscope_embeddings
            embeddings_type = "DashScope (阿里云通义千问)"
            print("✓ 使用 DashScope embeddings")
        else:
            raise Exception("DashScope连接失败")
    except Exception as dashscope_error:
        print("⚠ DashScope 不可用")
        
        # 方案2: 降级到SimpleEmbeddings
        print("⚠ 降级到 SimpleEmbeddings (TF-IDF)")
        print("  提示：为获得更好的检索效果，请使用：")
        print("  1. DashScope（推荐）: 在环境变量设置 DASHSCOPE_API_KEY")
        from browser_flow.handlers.rag.embeddings_manager import SimpleEmbeddings
        embeddings = SimpleEmbeddings()
        embeddings_type = "SimpleEmbeddings (TF-IDF)"

    # 创建向量存储
    print(f"正在生成文档向量（使用 {embeddings_type}）...")
    
    if isinstance(embeddings, DashScopeEmbeddings):
        vectorstore = FAISS.from_documents(documents, embeddings)
    else:
        vectorstore = FAISS.from_documents(documents, embeddings)
        
    print(f"✓ 已将 {len(documents)} 个文档块向量化并存储")

    # 创建检索器（使用 MMR 避免重复）
    print(f"\n=== 执行语义检索 ({config.search_type.upper()}) ===")
    
    search_kwargs = {"k": config.top_k}
    if config.search_type == "mmr":
        search_kwargs.update({
            "fetch_k": config.top_k * 2,  # 先获取更多候选，然后重排序
            "lambda_mult": 0.5,  # 平衡相关性和多样性
        })
    
    retriever = vectorstore.as_retriever(
        search_type=config.search_type,
        search_kwargs=search_kwargs
    )

    # 检索相关文档
    relevant_docs = retriever.get_relevant_documents(question)
    print(f"✓ 找到 {len(relevant_docs)} 个相关文档块")

    # 打印每个文档块的信息
    for index, doc in enumerate(relevant_docs):
        preview = doc.page_content[:100].replace("\n", " ")
        print(f"  {index + 1}. [块 {doc.metadata['chunk_index']}] {preview}...")

    # 构建提示词
    if prompt_type == "recruitment":
        template = PromptBuilder.build_recruitment_prompt()
    else:
        template = PromptBuilder.build_general_prompt()
    
    prompt_template = PromptTemplate(
        input_variables=["context", "question"],
        template=template
    )

    # 组合上下文
    context = "\n\n---\n\n".join(doc.page_content for doc in relevant_docs)

    # 使用LLM
    if llm is None:
        llm = llm_qwen

    print("\n=== 调用 大模型生成答案 ===\n")
    
    prompt = prompt_template.format(context=context, question=question)
    
    # 将字符串转换为消息对象
    from langchain.schema import HumanMessage
    messages = [HumanMessage(content=prompt)]
    result = llm.invoke(messages)

    return result.content if hasattr(result, 'content') else str(result)
