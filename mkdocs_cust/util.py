from parsel import Selector


def add_target_blank_to_links(html):
    """
    在给定的 HTML 中，为符合特定条件的 <a> 标签添加 target="_blank" 属性

    条件："a[href*='//']:not(.md-content__button):not(:has(img))"

    参数:
        html (str): 输入的 HTML 字符串

    返回:
        str: 处理后的 HTML 字符串
    """
    selector = Selector(text=html)

    # 查找所有符合条件的 a 标签
    links = selector.css("a[href*='//']:not(.md-content__button):not(:has(img))")

    for link in links:
        # 获取当前元素的完整 HTML
        original = link.get()
        # 创建一个新元素并添加 target="_blank"
        new_tag = original.replace("<a ", '<a target="_blank" ', 1)
        # 替换原始 HTML 中的内容
        html = html.replace(original, new_tag)

    return html


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
