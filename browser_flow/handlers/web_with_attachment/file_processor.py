"""
File download and parsing functions

Support for downloading and parsing multiple file formats with a unified parser system.
"""
import os
import logging
import requests
from urllib.parse import urlparse
from typing import List, Set, Dict, Callable, Optional
import pandas as pd
import PyPDF2
import docx
from browser_flow.handlers.web_with_attachment.data_models import Attachment

logger = logging.getLogger(__name__)


class FileParserRegistry:
    """文件解析器注册表 - 统一管理所有文件格式的解析器"""
    
    def __init__(self):
        self._parsers: Dict[str, Callable[[str], str]] = {}
        self._supported_extensions: Set[str] = set()
        self._register_default_parsers()
    
    def _register_default_parsers(self):
        """注册默认的文件解析器"""
        # Excel 文件
        self.register(['.xlsx', '.xls'], self._parse_excel_file)
        
        # PDF 文件
        self.register(['.pdf'], self._parse_pdf_file)
        
        # Word 文件
        self.register(['.docx', '.doc'], self._parse_word_file)
        
        # 文本文件
        self.register(['.txt', '.md', '.markdown'], self._parse_text_file)
        
        # CSV 文件
        self.register(['.csv'], self._parse_csv_file)
        
        # WPS 文件
        self.register(['.wps', '.et', '.dps'], self._parse_wps_file)
        
        # RTF 文件
        self.register(['.rtf'], self._parse_rtf_file)
        
        # HTML 文件
        self.register(['.html', '.htm'], self._parse_html_file)
        
        # XML 文件
        self.register(['.xml'], self._parse_xml_file)
        
        # JSON 文件
        self.register(['.json'], self._parse_json_file)
        
        # YAML 文件
        self.register(['.yaml', '.yml'], self._parse_yaml_file)
    
    def register(self, extensions: List[str], parser_func: Callable[[str], str]):
        """注册文件解析器"""
        for ext in extensions:
            ext_lower = ext.lower()
            self._parsers[ext_lower] = parser_func
            self._supported_extensions.add(ext_lower)
    
    def is_supported(self, extension: str) -> bool:
        """检查文件扩展名是否支持"""
        return extension.lower() in self._supported_extensions
    
    def get_supported_extensions(self) -> Set[str]:
        """获取所有支持的扩展名"""
        return self._supported_extensions.copy()
    
    def parse_file(self, file_path: str) -> str:
        """解析文件"""
        ext = os.path.splitext(file_path)[1].lower()
        
        if not self.is_supported(ext):
            logger.warning(f"不支持的文件格式: {ext}, 文件: {os.path.basename(file_path)}")
            return ""
        
        parser_func = self._parsers[ext]
        return parser_func(file_path)
    
    # 默认解析器实现
    def _parse_excel_file(self, file_path: str) -> str:
        """解析 Excel 文件"""
        logger.info(f"正在解析 Excel 文件: {os.path.basename(file_path)}...")
        try:
            df = pd.read_excel(file_path, sheet_name=None)
            content = ""
            
            for sheet_name, sheet_data in df.items():
                content += f"\n\n=== 工作表: {sheet_name} ===\n"
                for index, row in sheet_data.iterrows():
                    row_str = " | ".join(str(cell) if pd.notna(cell) else "" for cell in row)
                    if row_str.strip():
                        content += f"{row_str}\n"
            
            logger.debug(f"✓ Excel文件解析完成 ({len(content)} 字符)")
            return content
        except Exception as error:
            logger.error(f"✗ Excel文件解析失败: {error}")
            raise error
    
    def _parse_pdf_file(self, file_path: str) -> str:
        """解析 PDF 文件"""
        logger.info(f"正在解析 PDF 文件: {os.path.basename(file_path)}...")
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            logger.debug(f"✓ PDF文件解析完成 ({len(text)} 字符)")
            return text
        except Exception as error:
            logger.error(f"✗ PDF文件解析失败: {error}")
            raise error
    
    def _parse_word_file(self, file_path: str) -> str:
        """解析 Word 文件"""
        logger.info(f"正在解析 Word 文件: {os.path.basename(file_path)}...")
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            logger.debug(f"✓ Word文件解析完成 ({len(text)} 字符)")
            return text
        except Exception as error:
            logger.error(f"✗ Word文件解析失败: {error}")
            raise error
    
    def _parse_text_file(self, file_path: str) -> str:
        """解析文本文件"""
        logger.info(f"正在解析文本文件: {os.path.basename(file_path)}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.debug(f"✓ 文本文件解析完成 ({len(content)} 字符)")
            return content
        except Exception as error:
            logger.error(f"✗ 文本文件解析失败: {error}")
            raise error
    
    def _parse_csv_file(self, file_path: str) -> str:
        """解析 CSV 文件"""
        logger.info(f"正在解析 CSV 文件: {os.path.basename(file_path)}...")
        try:
            df = pd.read_csv(file_path)
            content = "\n"
            for _, row in df.iterrows():
                content += " | ".join(str(cell) if pd.notna(cell) else "" for cell in row) + "\n"
            logger.debug(f"✓ CSV文件解析完成 ({len(content)} 字符, {len(df)} 行)")
            return content
        except Exception as error:
            logger.error(f"✗ CSV文件解析失败: {error}")
            raise error
    
    def _parse_wps_file(self, file_path: str) -> str:
        """解析 WPS 文件"""
        logger.info(f"正在解析 WPS 文件: {os.path.basename(file_path)}...")
        try:
            with open(file_path, 'rb') as file:
                content = file.read()
            
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text = content.decode('gbk')
                except UnicodeDecodeError:
                    text = content.decode('utf-8', errors='ignore')
            
            import re
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            logger.debug(f"✓ WPS文件解析完成 ({len(text)} 字符)")
            return text
        except Exception as error:
            logger.error(f"✗ WPS文件解析失败: {error}")
            raise error
    
    def _parse_rtf_file(self, file_path: str) -> str:
        """解析 RTF 文件"""
        logger.info(f"正在解析 RTF 文件: {os.path.basename(file_path)}...")
        try:
            import re
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
            
            text = re.sub(r'\\[a-z]+\d*\s?', '', content)
            text = re.sub(r'[{}]', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            logger.debug(f"✓ RTF文件解析完成 ({len(text)} 字符)")
            return text
        except Exception as error:
            logger.error(f"✗ RTF文件解析失败: {error}")
            raise error
    
    def _parse_html_file(self, file_path: str) -> str:
        """解析 HTML 文件"""
        logger.info(f"正在解析 HTML 文件: {os.path.basename(file_path)}...")
        try:
            from bs4 import BeautifulSoup
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text()
            
            import re
            text = re.sub(r'\s+', ' ', text).strip()
            
            logger.debug(f"✓ HTML文件解析完成 ({len(text)} 字符)")
            return text
        except Exception as error:
            logger.error(f"✗ HTML文件解析失败: {error}")
            raise error
    
    def _parse_xml_file(self, file_path: str) -> str:
        """解析 XML 文件"""
        logger.info(f"正在解析 XML 文件: {os.path.basename(file_path)}...")
        try:
            import xml.etree.ElementTree as ET
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read().strip()
            
            if content.startswith('\ufeff'):
                content = content[1:]
            content = content.strip()
            
            root = ET.fromstring(content)
            text = ""
            for elem in root.iter():
                if elem.text and elem.text.strip():
                    text += elem.text.strip() + " "
            
            import re
            text = re.sub(r'\s+', ' ', text).strip()
            
            logger.debug(f"✓ XML文件解析完成 ({len(text)} 字符)")
            return text
        except Exception as error:
            logger.error(f"✗ XML文件解析失败: {error}")
            raise error
    
    def _parse_json_file(self, file_path: str) -> str:
        """解析 JSON 文件"""
        logger.info(f"正在解析 JSON 文件: {os.path.basename(file_path)}...")
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            text = json.dumps(data, ensure_ascii=False, indent=2)
            
            logger.debug(f"✓ JSON文件解析完成 ({len(text)} 字符)")
            return text
        except Exception as error:
            logger.error(f"✗ JSON文件解析失败: {error}")
            raise error
    
    def _parse_yaml_file(self, file_path: str) -> str:
        """解析 YAML 文件"""
        logger.info(f"正在解析 YAML 文件: {os.path.basename(file_path)}...")
        try:
            import yaml
            with open(file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
            
            text = yaml.dump(data, default_flow_style=False, allow_unicode=True)
            
            logger.debug(f"✓ YAML文件解析完成 ({len(text)} 字符)")
            return text
        except Exception as error:
            logger.error(f"✗ YAML文件解析失败: {error}")
            raise error


# 全局文件解析器实例
file_parser_registry = FileParserRegistry()


async def download_file(url: str, output_path: str) -> None:
    """
    下载文件
    
    Args:
        url: 文件URL
        output_path: 输出路径
    """
    # 检查文件是否已存在
    if os.path.exists(output_path) and os.path.isfile(output_path):
        stats = os.stat(output_path)
        file_size_mb = round(stats.st_size / 1024 / 1024, 2)
        logger.info(f"⊙ 文件已存在 ({file_size_mb} MB)，跳过下载: {os.path.basename(output_path)}")
        return

    logger.info(f"正在从 {url} 下载...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
            
        logger.info(f"✓ 下载完成: {os.path.basename(output_path)}")
    except Exception as error:
        logger.error(f"✗ 下载失败 {url}: {error}")
        raise error


def process_single_file(file_path: str, filename: str) -> str:
    """
    处理单个文件 - 统一的文件处理逻辑
    
    Args:
        file_path: 文件路径
        filename: 文件名
        
    Returns:
        str: 处理后的内容
    """
    try:
        logger.info(f"正在处理文件: {filename}")
        
        # 检查文件扩展名是否支持
        ext = os.path.splitext(filename)[1].lower()
        if not file_parser_registry.is_supported(ext):
            logger.warning(f"不支持的文件格式: {ext}, 文件: {filename}")
            return ""
        
        # 使用解析器注册表解析文件
        content = file_parser_registry.parse_file(file_path)
        
        # 如果解析返回空字符串，直接返回
        if not content:
            logger.info(f"文件解析结果为空: {filename}")
            return ""
        
        # 构建文件内容
        file_content = f"\n\n========================================\n"
        file_content += f"附件: {filename}\n"
        file_content += "========================================\n"
        file_content += content
        
        logger.info(f"✓ 文件处理完成: {filename}")
        return file_content
        
    except Exception as error:
        logger.error(f"处理文件失败: {filename}, 错误: {error}")
        return ""


def check_file_exists_by_name(downloads_dir: str, filename: str) -> bool:
    """
    检查指定文件名的文件是否已存在
    
    Args:
        downloads_dir: 下载目录路径
        filename: 要检查的文件名
        
    Returns:
        bool: 文件是否存在
    """
    if not os.path.exists(downloads_dir):
        return False
    
    file_path = os.path.join(downloads_dir, filename)
    return os.path.exists(file_path) and os.path.isfile(file_path)


def get_existing_files_by_names(downloads_dir: str, target_filenames: List[str]) -> List[str]:
    """
    根据目标文件名列表，检查哪些文件已存在
    
    Args:
        downloads_dir: 下载目录路径
        target_filenames: 目标文件名列表
        
    Returns:
        List[str]: 已存在的文件名列表
    """
    if not os.path.exists(downloads_dir):
        return []
    
    existing_files = []
    for filename in target_filenames:
        if check_file_exists_by_name(downloads_dir, filename):
            existing_files.append(filename)
    
    return existing_files


def parse_existing_files(downloads_dir: str, files: List[str]) -> str:
    """
    解析现有的文件内容
    
    Args:
        downloads_dir: 下载目录路径
        files: 文件列表
        
    Returns:
        str: 解析后的内容
    """
    xlsx_content = ""
    other_content = ""
    
    for filename in files:
        file_path = os.path.join(downloads_dir, filename)
        
        if not os.path.isfile(file_path):
            continue
        
        # 使用统一的文件处理逻辑
        file_content = process_single_file(file_path, filename)
        
        # 如果文件处理返回空字符串，跳过
        if not file_content:
            continue
        
        # 根据文件类型分类（Excel 文件优先）
        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.xlsx', '.xls']:
            xlsx_content += file_content
        else:
            other_content += file_content
    
    # 返回合并后的内容（xlsx内容优先）
    return xlsx_content + other_content


async def download_and_parse_attachments(attachments: List[Attachment], downloads_dir: str) -> str:
    """
    下载并解析所有附件
    
    Args:
        attachments: 附件列表
        downloads_dir: 下载目录
        
    Returns:
        str: 所有附件解析后的内容
    """
    # 确保downloads目录存在
    os.makedirs(downloads_dir, exist_ok=True)
    
    # 生成所有目标文件名
    target_filenames = []
    for attachment in attachments:
        if not attachment.url or attachment.url == 'N/A' or not attachment.url.startswith('http'):
            continue
            
        # 使用附件标题作为文件名（保留原始扩展名）
        url_path = urlparse(attachment.url).path
        url_filename = os.path.basename(url_path)
        ext = os.path.splitext(url_filename)[1]
        
        # 清理文件名中的非法字符，使用附件标题
        clean_title = attachment.title.replace('<', '_').replace('>', '_').replace(':', '_').replace('"', '_').replace('/', '_').replace('\\', '_').replace('|', '_').replace('?', '_').replace('*', '_')
        
        # 如果标题没有扩展名，添加扩展名
        if not os.path.splitext(clean_title)[1]:
            clean_title += ext
            
        target_filenames.append(clean_title)
    
    # 检查哪些文件已存在
    logger.info("=== 检查现有文件 ===")
    existing_files = get_existing_files_by_names(downloads_dir, target_filenames)
    
    if existing_files:
        logger.info(f"✓ 发现现有文件，直接使用: {existing_files}")
        # 解析现有文件
        return parse_existing_files(downloads_dir, existing_files)
    
    # 如果没有现有文件，则下载新文件
    logger.info("=== 开始下载附件 ===")
    
    xlsx_content = ""  # 优先处理 xlsx/xls 文件（岗位信息表）
    other_content = ""  # 其他文件
    processed_files: Set[str] = set()  # 记录已处理的文件

    for attachment in attachments:
        # 跳过无效的URL
        if not attachment.url or attachment.url == 'N/A' or not attachment.url.startswith('http'):
            logger.info(f"⚠ 跳过无效URL的附件: {attachment.title}")
            continue

        # 使用附件标题作为文件名（保留原始扩展名）
        url_path = urlparse(attachment.url).path
        url_filename = os.path.basename(url_path)
        ext = os.path.splitext(url_filename)[1]
        
        # 清理文件名中的非法字符，使用附件标题
        clean_title = attachment.title.replace('<', '_').replace('>', '_').replace(':', '_').replace('"', '_').replace('/', '_').replace('\\', '_').replace('|', '_').replace('?', '_').replace('*', '_')
        
        # 如果标题没有扩展名，添加扩展名
        if not os.path.splitext(clean_title)[1]:
            clean_title += ext
            
        filename = clean_title
        file_path = os.path.join(downloads_dir, filename)

        try:
            # 下载文件
            await download_file(attachment.url, file_path)

            # 使用统一的文件处理逻辑
            file_content = process_single_file(file_path, filename)
            
            # 如果文件处理返回空字符串，跳过
            if not file_content:
                continue
            
            # 根据文件类型分类
            ext_lower = os.path.splitext(filename)[1].lower()
            if ext_lower in ['.xlsx', '.xls']:
                xlsx_content += file_content
            else:
                other_content += file_content
                
            # 记录已处理的文件
            processed_files.add(filename)
        except Exception as error:
            logger.error(f"处理附件失败: {attachment.title}, 错误: {error}")
            # 不添加错误信息到内容中，直接跳过

    # 扫描downloads目录，处理所有未被处理的文件
    logger.info("\n=== 扫描downloads目录查找未处理的文件 ===")
    try:
        existing_files = os.listdir(downloads_dir)
        
        for filename in existing_files:
            if filename in processed_files:
                continue  # 已处理，跳过
                
            file_path = os.path.join(downloads_dir, filename)
            
            if not os.path.isfile(file_path):
                continue  # 不是文件，跳过
                
            # 使用统一的文件处理逻辑
            file_content = process_single_file(file_path, filename)
            
            # 如果文件处理返回空字符串，跳过
            if not file_content:
                continue
            
            # 根据文件类型分类
            ext_lower = os.path.splitext(filename)[1].lower()
            if ext_lower in ['.xlsx', '.xls']:
                xlsx_content += file_content
            else:
                other_content += file_content
                
            processed_files.add(filename)
            logger.info(f"✓ 已处理文件: {filename}")
    except Exception as error:
        logger.error('扫描downloads目录时出错:', error)

    # 返回时将xlsx内容放在最前面，确保重要信息不会因为上下文截断而丢失
    return xlsx_content + other_content
