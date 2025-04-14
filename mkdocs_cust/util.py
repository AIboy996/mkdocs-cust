from __future__ import annotations
from parsel import Selector
import re
from lxml import html
from typing import TypedDict


def pretifier(func):
    """装饰器，标准化html文本格式"""

    def prettify_html(html_text: str, *args, **kwargs):
        html_text = html.tostring(html.fromstring(html_text), encoding="unicode")
        return func(html_text, *args, **kwargs)

    return prettify_html


@pretifier
def add_target_blank_to_links(raw_html_text: str):
    """
    在给定的 HTML 中，为符合特定条件的 <a> 标签添加 target="_blank" 属性

    xpath选择器："//a[contains(@href, '//') and not(contains(@class, 'md-content__button')) and not(img)]"

    参数:
        html (str): 输入的 HTML 字符串

    返回:
        str: 处理后的 HTML 字符串
    """
    selector = Selector(text=raw_html_text)

    # 查找所有符合条件的 a 标签
    links = selector.xpath(
        "//a[contains(@href, '//') and not(contains(@class, 'md-content__button')) and not(img)]"
    )

    for link in links:
        original = link.get()
        # 创建一个新元素并添加 target="_blank"
        element = html.fromstring(original)
        element.set("target", "_blank")
        new_tag = html.tostring(element, encoding="unicode")
        # 替换原始 HTML 中的内容
        raw_html_text = raw_html_text.replace(original, new_tag)

    return raw_html_text


def get_body(raw_html_text):
    """
    从HTML中提取body部分
    """
    # 使用lxml解析HTML
    tree = html.fromstring(raw_html_text)
    # 提取body部分
    body = tree.xpath("//body")[0]
    # 将body转换为字符串
    body_str = html.tostring(body, encoding="unicode")
    return body_str


@pretifier
def get_meta(raw_html_text):
    tree = Selector(raw_html_text)
    first_markdown_cell = tree.css(
        ".jp-Cell.jp-MarkdownCell .jp-RenderedHTMLCommon"
    ).get()
    meta_dict = {}
    if first_markdown_cell:
        # 使用正则表达式提取两个<hr/>标签之间的内容
        match = re.search(r"<hr>(.*?)<hr>", first_markdown_cell, re.DOTALL)
        if match:
            content_between_hr = match.group(1).strip()
            meta_selector = Selector(text=content_between_hr)
            # 提取<p>标签内容作为键
            for p_tag in meta_selector.xpath("//p"):
                key = p_tag.xpath("text()").get().strip(":")
                # 提取对应的<ul>标签内容作为值
                ul_tag = p_tag.xpath("following-sibling::ul[1]")
                if ul_tag:
                    values = ul_tag.xpath(".//li/text()").getall()
                    meta_dict[key] = values
            # 删除掉meta信息
            return raw_html_text.replace(first_markdown_cell, ""), meta_dict
    return raw_html_text, meta_dict


def ipynb_to_html(path):
    """
    将ipynb文件转换为html
    """
    import nbformat
    from nbconvert import HTMLExporter

    # 读取ipynb文件
    with open(path, "r", encoding="utf-8") as f:
        notebook_content = nbformat.read(f, as_version=4)

    # 创建HTML导出器
    html_exporter = HTMLExporter()
    html_exporter.template_name = "lab"

    # 转换为HTML
    # 暂时不处理额外用到的资源
    (raw_html, resources) = html_exporter.from_notebook_node(notebook_content)
    body = get_body(raw_html)
    reduced_body, meta = get_meta(body)
    return reduced_body, meta


class _TocToken(TypedDict):
    level: int
    id: str
    name: str
    children: list[_TocToken]


def format_toc(toc: list) -> _TocToken:
    res: _TocToken = {"level": 0, "id": "", "name": "", "children": []}
    stack = [res]

    for item in toc:
        while stack and stack[-1]["level"] >= item["level"]:
            stack.pop()
        new_token: _TocToken = {**item, "children": []}
        stack[-1]["children"].append(new_token)
        stack.append(new_token)
    assert (len(res["children"]) == 1) and (res["children"][0]["level"] == 1), (
        "Document should start with h1 element and have precisely one h1 element."
    )
    return res["children"]


def get_toc_tokens(html_content):
    # Initialize TOC list
    toc = []

    # Regular expression to match header tags (h1-h6)
    header_pattern = r'<(h[1-6])(?:\s+id="([^"]*)")?\s*>(.*?)</\1>'

    # Find all headers
    headers = re.findall(header_pattern, html_content, re.IGNORECASE | re.DOTALL)

    for header in headers:
        # Extract tag, id (if present), and text
        tag, anchor, text = header
        # Get header level (1-6)
        level = int(tag[1])
        # Clean text by removing extra whitespace
        text = " ".join(text.strip().split())
        text = re.sub(r"<[^>]+>", "", text).replace("¶", "")  # Remove HTML tags
        # Add to TOC
        toc.append({"level": level, "name": text, "id": anchor})
    return format_toc(toc)
