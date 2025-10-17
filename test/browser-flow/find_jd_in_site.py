import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from browser_flow import BrowserFlow, run_workflow

async def find_jd() -> None:
    try:
        flow = BrowserFlow()
        result = await flow.run("""工作语言是中文，进入https://hrss.jl.gov.cn/，找到这个网站上今年的应届生招聘信息，
        如果没有招聘相关的链接，就选择使用搜索框搜索招聘，没有搜索框就直接进入公告相关页面中查询，找到页面后调用RAG工具找艺术生相关岗位。""", max_steps=10)
        print(result)
    except Exception as e:
        print(e)

if __name__ == '__main__':
    asyncio.run(find_jd())
