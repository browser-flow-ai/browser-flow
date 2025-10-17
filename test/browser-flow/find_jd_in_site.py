import asyncio

from browser_flow import BrowserFlow, run_workflow

async def find_jd() -> None:
    try:
        flow = BrowserFlow()
        result = await flow.run("工作语言是中文，进入https://hrss.jl.gov.cn/，并找到这个网站上今年的应届生招聘信息，并验证是否招收艺术类考生。")
        print(result)
    except Exception as e:
        print(e)

if __name__ == '__main__':
    asyncio.run(find_jd())
