from parsel import Selector
from lxml import html


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


if __name__ == "__main__":
    sample_html = """
    <div class="md-content">
        <a href="https://example.com">外部链接1</a>
        <a href="https://example.com" class="md-content__button">按钮链接</a>
        <a href="/internal">内部链接</a>
        <a href="https://example.com"><img src="url" alt="alternatetext"/></a>
        <a href="http://another.com">外部链接2</a>
    </div>
    """

    processed_html = add_target_blank_to_links(sample_html)
    print(processed_html)
