import json

import trafilatura

def run_trafilatura():
    """Run trafilatura to extract text and links from a webpage"""
    url = "https://hrss.yn.gov.cn/html/2025/9/2/62889.html"
    downloaded = trafilatura.fetch_url(url)          # Fetch HTML (with redirect and compression handling)
    
    # Extract text content
    text = trafilatura.extract(downloaded)
    print("Extracted text content:")
    print(text)
    print("----------------------------")
    
    # Extract links - using Markdown format
    md_output = trafilatura.extract(
        downloaded,
        output_format='markdown',
        with_metadata=True,
        include_links=True,
        include_tables=True
    )
    
    # Extract links from Markdown
    import re
    md_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', md_output)
    print(f"Number of extracted links: {len(md_links)}")
    print("Link list:")
    for i, (text, link) in enumerate(md_links):
        print(f"  {i+1}. {text} -> {link}")
    
    return {
        'text': text,
        'links': md_links
    }

if __name__ == '__main__':
    run_trafilatura()