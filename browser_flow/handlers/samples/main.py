#!/usr/bin/env python3
"""
云南招聘信息智能问答系统 - 主程序入口

基于 RAG 技术的智能问答系统，支持多种文件格式解析和智能嵌入方案选择
"""

import asyncio
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from browser_flow.handlers.samples.workflow import process_url_rag

async def main():
    """主函数"""
    base_url = "https://hrss.yn.gov.cn"
    url = "https://hrss.yn.gov.cn/html/2025/9/2/62889.html"
    question = "招收艺术设计的应届毕业生吗？"
    
    print("=== 开始使用 RAG 处理问题 ===")
    print(f"问题: {question}")
    
    # 重试机制
    max_retries = 2
    for attempt in range(max_retries):
        try:
            print(f"\n尝试 {attempt + 1}/{max_retries}...")
            answer = await process_url_rag(base_url, url, question)
            
            print("\n" + "=" * 60)
            print("📝 答案")
            print("=" * 60)
            print(answer)
            print("=" * 60)
            return
            
        except Exception as error:
            print(f"✗ 处理失败 (尝试 {attempt + 1}/{max_retries}): {error}")
            if attempt < max_retries - 1:
                print("⏳ 等待 3 秒后重试...")
                await asyncio.sleep(3)
            else:
                print("✗ 所有重试都失败了")

if __name__ == "__main__":
    asyncio.run(main())
