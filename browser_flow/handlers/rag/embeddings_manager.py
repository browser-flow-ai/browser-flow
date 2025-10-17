"""
嵌入管理器 - 统一管理多种嵌入方案

支持：
1. DashScope Embeddings（高质量中文语义理解）
2. SimpleEmbeddings（本地TF-IDF降级方案）

自动选择最佳可用的嵌入方案
"""

import os
import logging
import asyncio
import aiohttp
import re
import math
from typing import List, Optional
from langchain.embeddings.base import Embeddings

logger = logging.getLogger(__name__)


class DashScopeEmbeddings(Embeddings):
    """DashScope Embeddings 实现"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        初始化 DashScope Embeddings
        
        Args:
            api_key: API密钥，如果为None则从环境变量DASHSCOPE_API_KEY获取
            model_name: 模型名称，如果为None则从环境变量DASHSCOPE_MODEL_NAME获取，默认为text-embedding-v2
            base_url: API基础URL，如果为None则从环境变量DASHSCOPE_BASE_URL获取
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY", "")
        self.model_name = model_name or os.getenv("DASHSCOPE_MODEL_NAME", "text-embedding-v2")
        self.base_url = base_url or os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding")
        
        if not self.api_key:
            logger.warning("未配置 DASHSCOPE_API_KEY")

    async def _call_api(self, texts: List[str]) -> List[List[float]]:
        """
        调用 DashScope API 进行文本向量化
        
        Args:
            texts: 要向量化的文本列表
            
        Returns:
            List[List[float]]: 向量列表
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": self.model_name,
                "input": {
                    "texts": texts
                }
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.post(self.base_url, headers=headers, json=data) as response:
                    response_data = await response.json()
                    
                    # 检查响应状态
                    if "code" in response_data:
                        raise Exception(f"DashScope API 错误 ({response_data['code']}): {response_data.get('message', 'Unknown error')}")
                    
                    # 提取 embeddings
                    embeddings = [item["embedding"] for item in response_data["output"]["embeddings"]]
                    return embeddings
                    
        except aiohttp.ClientError as e:
            raise Exception(f"DashScope API 请求失败: {e}")
        except Exception as e:
            raise Exception(f"DashScope Embeddings 错误: {e}")

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量向量化文档（异步版本）
        
        Args:
            texts: 要向量化的文本列表
            
        Returns:
            List[List[float]]: 向量列表
        """
        # DashScope API 每次最多支持的文本数量（可通过环境变量配置）
        batch_size = int(os.getenv("DASHSCOPE_BATCH_SIZE", "25"))
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.info(f"正在向量化文档 {i + 1}-{min(i + batch_size, len(texts))}/{len(texts)} (使用 DashScope)")

            embeddings = await self._call_api(batch)
            all_embeddings.extend(embeddings)

            # 避免请求过快，延迟时间可通过环境变量配置
            delay = float(os.getenv("DASHSCOPE_DELAY", "0.1"))
            if i + batch_size < len(texts):
                await asyncio.sleep(delay)

        return all_embeddings

    async def aembed_query(self, text: str) -> List[float]:
        """
        向量化单个查询（异步版本）
        
        Args:
            text: 要向量化的文本
            
        Returns:
            List[float]: 向量
        """
        embeddings = await self._call_api([text])
        return embeddings[0]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量向量化文档（同步版本）
        
        Args:
            texts: 要向量化的文本列表
            
        Returns:
            List[List[float]]: 向量列表
        """
        try:
            loop = asyncio.get_running_loop()
            # 如果已经在事件循环中，使用 run_in_executor
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.aembed_documents(texts))
                return future.result()
        except RuntimeError:
            # 如果没有运行的事件循环，直接使用 asyncio.run
            return asyncio.run(self.aembed_documents(texts))

    def embed_query(self, text: str) -> List[float]:
        """
        向量化单个查询（同步版本）
        
        Args:
            text: 要向量化的文本
            
        Returns:
            List[float]: 向量
        """
        try:
            loop = asyncio.get_running_loop()
            # 如果已经在事件循环中，使用 run_in_executor
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.aembed_query(text))
                return future.result()
        except RuntimeError:
            # 如果没有运行的事件循环，直接使用 asyncio.run
            return asyncio.run(self.aembed_query(text))

    async def test_connection(self) -> bool:
        """
        测试 API 连接是否正常
        
        Returns:
            bool: 连接是否成功
        """
        try:
            if not self.api_key:
                logger.error("✗ 未配置 DASHSCOPE_API_KEY")
                return False

            # 测试简单的向量化
            await self.aembed_query("测试连接")
            logger.info(f"✓ DashScope Embeddings ({self.model_name}) 连接成功")
            return True
        except Exception as e:
            logger.error(f"✗ DashScope Embeddings 连接失败: {e}")
            return False


class SimpleEmbeddings(Embeddings):
    """简单的本地 Embeddings 实现，使用 TF-IDF 风格的向量化方法"""
    
    def __init__(self, vector_size: Optional[int] = None):
        """
        初始化 SimpleEmbeddings
        
        Args:
            vector_size: 向量维度，如果为None则从环境变量SIMPLE_EMBEDDINGS_VECTOR_SIZE获取，默认为384
        """
        self.vector_size = vector_size or int(os.getenv("SIMPLE_EMBEDDINGS_VECTOR_SIZE", "384"))
        self.vocabulary = {}  # 词汇表
        self.idf = {}  # IDF 值
        self.doc_count = 0  # 文档总数
        
    def tokenize(self, text: str) -> List[str]:
        """
        简单的文本分词
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 分词结果
        """
        # 移除标点和特殊字符，转小写，分词
        # 支持中文字符 \u4e00-\u9fa5
        text = text.lower()
        text = re.sub(r'[^\w\s\u4e00-\u9fa5]', ' ', text)
        tokens = text.split()
        return [token for token in tokens if len(token) > 0]
    
    def hash_token(self, token: str, seed: int) -> int:
        """
        计算文本的哈希值（用于生成向量特征）
        
        Args:
            token: 词汇
            seed: 种子值
            
        Returns:
            int: 哈希值
        """
        hash_val = seed
        for char in token:
            hash_val = (hash_val * 31 + ord(char)) % self.vector_size
        return abs(hash_val)
    
    def text_to_vector(self, text: str) -> List[float]:
        """
        将文本转换为向量
        
        Args:
            text: 输入文本
            
        Returns:
            List[float]: 向量
        """
        vector = [0.0] * self.vector_size
        tokens = self.tokenize(text)
        
        if len(tokens) == 0:
            return vector
        
        # 使用多个哈希函数来增加特征丰富度
        num_hashes = 3
        for token in tokens:
            for seed in range(num_hashes):
                index = self.hash_token(token, seed)
                vector[index] += 1.0 / len(tokens)  # TF (Term Frequency)
        
        # L2 归一化
        norm = math.sqrt(sum(val * val for val in vector))
        if norm > 0:
            vector = [val / norm for val in vector]
        
        return vector
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        将文档列表转换为向量
        
        Args:
            texts: 文档列表
            
        Returns:
            List[List[float]]: 向量列表
        """
        print(f"正在向量化 {len(texts)} 个文档...")
        return [self.text_to_vector(text) for text in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """
        将查询文本转换为向量
        
        Args:
            text: 查询文本
            
        Returns:
            List[float]: 向量
        """
        return self.text_to_vector(text)
    
    def __call__(self, texts: List[str]) -> List[List[float]]:
        """
        使 SimpleEmbeddings 对象可调用，兼容 LangChain 接口
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 向量列表
        """
        return self.embed_documents(texts)


class EmbeddingsManager:
    """嵌入管理器 - 自动选择最佳嵌入方案"""
    
    def __init__(self):
        """初始化嵌入管理器"""
        self.embeddings = None
        self.embeddings_type = "unknown"
    
    async def get_embeddings(self) -> Embeddings:
        """
        获取最佳可用的嵌入方案
        
        Returns:
            Embeddings: 嵌入对象
        """
        if self.embeddings is not None:
            return self.embeddings
        
        # 方案1: 尝试使用 DashScope（最佳：阿里云通义千问，高质量中文支持）
        try:
            dashscope_embeddings = DashScopeEmbeddings()
            is_connected = await dashscope_embeddings.test_connection()
            if is_connected:
                self.embeddings = dashscope_embeddings
                self.embeddings_type = "DashScope（阿里云通义千问）"
                logger.info("✓ 使用 DashScope embeddings")
                return self.embeddings
            else:
                logger.info("⚠ DashScope 连接失败，降级到 SimpleEmbeddings...")
                raise Exception("DashScope连接失败")
        except Exception as dashscope_error:
            logger.info(f"⚠ DashScope 不可用: {dashscope_error}")
            
            # 方案2: 降级到 SimpleEmbeddings（参考 TypeScript 实现）
            logger.info("⚠ 降级到 SimpleEmbeddings (TF-IDF 风格)")
            logger.info("  提示：为获得更好的检索效果，请使用：")
            logger.info("  1. DashScope（推荐）: 在环境变量设置 DASHSCOPE_API_KEY")
            try:
                self.embeddings = SimpleEmbeddings()
                self.embeddings_type = "SimpleEmbeddings (TF-IDF 风格)"
                logger.info("✓ 使用 SimpleEmbeddings (TF-IDF 风格)")
                return self.embeddings
            except Exception as simple_error:
                logger.error(f"✗ SimpleEmbeddings 初始化失败: {simple_error}")
                raise Exception("无法初始化任何嵌入方案")
    
    def get_embeddings_type(self) -> str:
        """获取当前使用的嵌入类型"""
        return self.embeddings_type
