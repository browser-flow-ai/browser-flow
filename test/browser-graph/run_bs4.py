from bs4 import BeautifulSoup
import requests

def run_1():
    html = '<div><h1>Title</h1><p>Para</p></div>'
    soup = BeautifulSoup(html, 'lxml')  # 用 lxml 解析器以获更好性能
    title = soup.h1.get_text()
    paras = [p.get_text() for p in soup.select('p')]
    print(title)
    print(paras)

def run_2():
    url = "https://hrss.yn.gov.cn/html/2025/9/2/62889.html"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    
    # 设置正确的编码
    resp.encoding = 'utf-8'

    soup = BeautifulSoup(resp.text, "lxml")

    articles = []

    for a in soup.select("#Body_ltl_newsContent a[href]"):
        articles.append({"downloads": a.get_text(strip=True), "href": a["href"]})

    print(articles)

if __name__ == '__main__':
    run_2()