from urllib.parse import urljoin
from browser_flow.handlers.web_with_attachment.data_models import JobPosting, Attachment
from pydantic import BaseModel, Field

from browser_control.agent_hand import AgentHand
from browser_wrapper.utils.deep_locator_utils import deep_locator
from browser_common.browser_logging import get_logger
logger = get_logger("browser_flow.handlers.web_extractor", enable_file_logging=False)


class BasicInfoSchema(BaseModel):
    """Schema for basic page information extraction."""
    title: str = Field(description="文章标题")
    content: str = Field(description="文章的完整内容，包括所有章节和详细信息")


async def extract_job_posting(base_url: str, url: str) -> JobPosting:
    hand = AgentHand("job_extraction_fetch_task")
    await hand.init()
    
    try:
        try:
            await hand.goto(url)
        except Exception as e:
            try:
                logger.error(f"navigate timeout error: {e}")
                await hand.goto(url)
            except Exception as e:
                logger.error(f"navigate timeout error: {e}")
                raise e

        basic_info = await hand.extract({
            "instruction": (
                "提取文章标题和完整的文章内容。确保提取完整内容而不截断。"
                "可以删除多余的大块回车符和换行符。"
            ),
            "output_schema": BasicInfoSchema
        })

        logger.info("基本信息提取成功")
        logger.info(f"提取结果类型: {type(basic_info)}")
        logger.info(f"提取结果内容: {basic_info}")
        
        # 直接从 Pydantic Schema 对象中获取数据
        title = basic_info.title
        content = basic_info.content
        
        logger.info(f"标题: {title}")
        logger.info(f"内容长度: {len(content)} 字符")

        # 等待动态内容加载
        await hand.stagehand.page.wait_for_timeout(2000)
        
        # 查找附件元素
        logger.info("正在查找附件链接...")
        attachment_elements = await hand.observe({
            "instruction": (
                "查找页面上所有可点击的下载链接（带有href属性的<a>标签）用于附件下载。"
                "寻找类似'附件1：...xlsx'、'附件2：...pdf'等文本的链接。"
                "这些链接允许用户下载文件。只查找<a>标签，不是<p>或其他元素。"
            )
        })
        
        logger.info(f"找到 {len(attachment_elements)} 个附件元素")

        # 从附件元素中获取实际的href链接
        attachments = []
        for i, element in enumerate(attachment_elements):
            try:
                logger.info(f"\n=== 处理元素 {i + 1}/{len(attachment_elements)} ===")
                logger.info(f"描述: {element.get('description', 'N/A')}")
                logger.info(f"选择器: {element.get('selector', 'N/A')}")
                
                # 从选择器中提取xpath（移除'xpath='前缀）
                xpath = element.get('selector', '').replace('xpath=', '')
                locator = deep_locator(hand.stagehand.page, xpath)
                
                # 等待元素可见
                try:
                    await locator.wait_for(state='visible', timeout=3000)
                except:
                    pass
                
                # 获取元素信息
                text = await locator.text_content()
                tag_name = await locator.evaluate("el => el.tagName")
                outer_html = await locator.evaluate("el => el.outerHTML.substring(0, 200)")
                
                logger.info(f"文本内容: {text}")
                logger.info(f"标签名: {tag_name}")
                logger.info(f"HTML片段: {outer_html}")
                
                # 如果不是 <a> 标签，尝试在内部查找 <a> 标签
                actual_locator = locator
                if tag_name != 'A':
                    logger.info("元素不是<a>标签，在内部搜索<a>标签...")
                    inner_link = locator.locator('a').first
                    inner_link_count = await locator.locator('a').count()
                    if inner_link_count > 0:
                        actual_locator = inner_link
                        logger.info("✓ 在内部找到<a>标签，使用它")
                    else:
                        logger.warning("内部未找到<a>标签")
                
                # 尝试使用多种方法获取href
                href = await actual_locator.get_attribute('href')
                logger.info(f"直接href: {href}")
                
                # 如果没有href，尝试从父元素获取
                if not href:
                    parent = actual_locator.locator('..')
                    try:
                        href = await parent.get_attribute('href')
                        logger.info(f"父元素href: {href}")
                    except:
                        pass
                
                # 尝试其他常见属性
                if not href:
                    try:
                        href = await actual_locator.get_attribute('data-url')
                        logger.info(f"data-url: {href}")
                    except:
                        pass
                        
                if not href:
                    try:
                        href = await actual_locator.get_attribute('data-href')
                        logger.info(f"data-href: {href}")
                    except:
                        pass

                # 如果仍然没有找到href，跳过
                if not href:
                    logger.warning(f"未找到href: {text or element.get('description', 'N/A')}")
                    continue

                # 从实际链接元素获取最终文本
                final_text = text if tag_name == 'A' else await actual_locator.text_content()
                final_text = final_text or element.get('description', 'N/A')

                # 将相对URL转换为绝对URL
                full_url = href
                if not href.startswith(('http://', 'https://')):
                    # 这是相对路径，添加基础URL
                    full_url = urljoin(base_url, href)

                attachments.append(Attachment(
                    title=final_text,
                    url=full_url
                ))
                
                logger.info(f"✓ 附件: {final_text} -> {full_url}")
                
            except Exception as error:
                logger.error(f'获取附件信息失败: {error}')

        result = JobPosting(
            title=title,
            content=content,
            attachments=attachments
        )

        logger.info("提取完成!")
        logger.info(f"结果: {result}")
        
        return result
        
    finally:
        await hand.close()
