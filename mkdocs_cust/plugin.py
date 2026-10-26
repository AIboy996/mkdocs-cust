from mkdocs import plugins
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from mkdocs.structure.toc import get_toc
from mkdocs.structure.files import File, Files

import logging
import os
import re
import subprocess
from html import escape

from mkdocs_cust.util import (
    add_target_blank_to_links,
    ipynb_to_html,
    get_toc_tokens,
    get_all_glightbox,
)


logger = logging.getLogger("mkdocs.plugins.mkdocs-cust")


class NotebookFile(File):
    """
    Wraps a regular File object to make .ipynb files appear as
    valid documentation files.

    refer to: https://github.com/danielfrg/mkdocs-jupyter/blob/a3cded5b3a7b14327196c98ffbc7558ce7d267ae/src/mkdocs_jupyter/plugin.py#L19
    """

    def __init__(self, file, use_directory_urls, site_dir, **kwargs):
        self.file = file
        self.dest_path = self._get_dest_path(use_directory_urls)
        self.abs_dest_path = os.path.normpath(os.path.join(site_dir, self.dest_path))
        self.url = self._get_url(use_directory_urls)

    def __getattr__(self, item):
        return self.file.__getattribute__(item)

    def is_documentation_page(self):
        return True


# Check events: https://www.mkdocs.org/dev-guide/plugins/#events


class CustPlugin(BasePlugin):
    config_scheme = (
        ("external_link_target_blank", config_options.Type(bool, default=True)),
        ("convert_ipynb", config_options.Type(bool, default=True)),
        ("webp_redirect", config_options.Type(bool, default=True)),
    )

    def on_files(self, files, *, config):
        if self.config["convert_ipynb"]:
            return Files(
                [
                    NotebookFile(file, **config)
                    if file.src_uri.endswith(".ipynb")
                    else file
                    for file in files
                ]
            )
        else:
            return files

    def on_pre_page(self, page, *, config, files):
        if page.file.src_uri.endswith(".ipynb"):
            page.read_source = lambda x: None
            page.markdown, meta = ipynb_to_html(page.file.abs_src_path)
            meta.update({"source_file": "ipynb"})
            page.meta = meta
        return page

    @plugins.event_priority(50)
    def on_page_content(self, html, *, page, config, files):
        if self.config["external_link_target_blank"]:
            html = add_target_blank_to_links(html)
        if page.file.src_uri.endswith(".ipynb"):
            toc_tokens = get_toc_tokens(html)
            page.toc = get_toc(toc_tokens)
        return html

    def on_post_page(self, output, *, page, config):
        ai_coauthors = self._get_ai_coauthors(page.file.abs_src_path, config["docs_dir"])
        if ai_coauthors:
            credits = self._render_ai_coauthor_credit(ai_coauthors)
            output = re.sub(
                r"</h1>",
                # The credit floats inside the <h1>, so it does not add to the
                # heading's height. A clearing spacer below keeps following
                # content (and mobile layouts) from overlapping the credit.
                lambda match: credits + match.group(0) + (
                    '<div aria-hidden="true" class="ai-coauthor-clearance" '
                    'style="clear:both;height:0;margin:0;padding:0"></div>'
                ),
                output,
                count=1,
                flags=re.IGNORECASE,
            )
            signature_style = (
                "<style>"
                "@keyframes ai-coauthor-signature-write {"
                "from { clip-path: inset(0 100% 0 0); opacity: .35; }"
                "to { clip-path: inset(0 0 0 0); opacity: 1; }"
                "}"
                ".ai-coauthor-signature { display: inline-block; animation: "
                "ai-coauthor-signature-write 1s cubic-bezier(.2,.75,.3,1) both; }"
                "@media (prefers-reduced-motion: reduce) {"
                ".ai-coauthor-signature { animation: none; }"
                "}"
                "</style>"
            )
            output = re.sub(
                r"</head>",
                lambda match: signature_style + match.group(0),
                output,
                count=1,
                flags=re.IGNORECASE,
            )

        glightbox = get_all_glightbox(output)

        def check_file(png_path):
            """the png_path is relative to the page url, we need to convert it to absolute path"""
            real_path_lst = png_path.split(os.sep)[1:]
            if real_path_lst:
                real_webp_relative_path = os.path.join(*real_path_lst) + ".webp"
            else:
                return False
            page_dir = os.path.dirname(page.file.abs_src_path)
            webp_path_abs = os.path.join(page_dir, real_webp_relative_path)
            return os.path.exists(webp_path_abs)

        for node, img_path in glightbox:
            if img_path.endswith(".png") and check_file(img_path):
                new_img_path = img_path + ".webp"
                new_tag = self.right_replace(node, img_path, new_img_path, 1)
                output = output.replace(node, new_tag)

        return output

    @staticmethod
    def _render_ai_coauthor_credit(coauthors):
        labels = ", ".join(
            'Co-authored by '
            f'<span class="ai-coauthor-signature" style="font-family:\'Chalkboard SE\',\'Comic Sans MS\',\'Segoe Print\',cursive;'
            f'font-style:normal;font-size:1.15em">{escape(tool_name)}</span>'
            for tool_name, _, _ in coauthors
        )
        popup_text = escape(
            "Git commit co-authors:\n" + "\n".join(
                f"{author_name} <{email}> (recognized as {tool_name})"
                for tool_name, author_name, email in coauthors
            ),
            quote=True,
        )
        return (
            '<button type="button" class="ai-coauthor-credit" '
            'style="float:right;appearance:none;border:0;padding:0;margin:.35em 0 0 .8em;'
            'background:transparent;cursor:pointer;font:inherit;line-height:inherit;'
            'text-align:right" '
            f'data-info="{popup_text}" onclick="window.alert(this.dataset.info)">'
            '<small style="color:#252525;font-size:.52em;font-weight:500">'
            f'{labels}</small></button>'
        )

    @staticmethod
    def _get_ai_coauthors(source_path, docs_dir):
        """Return the AI co-author with the most co-authored commits.

        Counts are aggregated by recognized AI tool, not by the exact
        ``Co-authored-by`` name/email, so variants such as "Claude" and
        "Claude Code" belong to the same signer. Ties are broken by the AI
        whose first co-authored commit is earliest.
        """
        try:
            result = subprocess.run(
                ["git", "log", "--reverse", "--format=%B%x00", "--",
                 os.path.relpath(source_path, docs_dir)],
                cwd=docs_dir,
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            return []

        ai_tools = {
            "Claude": ("claude", "anthropic"),
            "Copilot": ("copilot",),
            "ChatGPT": ("chatgpt",),
            "Codex": ("codex", "openai", "gpt"),
            "Gemini": ("gemini",),
            "Cursor": ("cursor",),
            "Devin": ("devin",),
            "DeepSeek": ("dsh", "deepseek"),
        }

        # Git log with --reverse lists commits oldest first, so the first time
        # an AI is seen is its earliest commit. Keep the name/email from that
        # occurrence for the credit popup.
        stats = {}
        for commit_index, message in enumerate(result.stdout.split("\0")):
            commit_tools = {}
            for line_index, line in enumerate(message.splitlines()):
                match = re.match(r"\s*Co-authored-by:\s*(.*?)\s*<([^>]+)>\s*$", line, re.IGNORECASE)
                if not match:
                    continue
                name, email = match.groups()
                identity_text = f"{name} {email}".lower()
                display_name = next(
                    (
                        tool
                        for tool, keywords in ai_tools.items()
                        if any(keyword in identity_text for keyword in keywords)
                    ),
                    None,
                )
                # Count each AI once per commit, even if it appears more than
                # once (or under different names) in the same commit.
                if display_name and display_name not in commit_tools:
                    commit_tools[display_name] = (
                        name.strip() or email.strip(),
                        email.strip(),
                        line_index,
                    )

            for tool, (name, email, line_index) in commit_tools.items():
                entry = stats.get(tool)
                if entry is None:
                    stats[tool] = {
                        "count": 1,
                        "first_index": commit_index,
                        "first_line": line_index,
                        "name": name,
                        "email": email,
                    }
                else:
                    entry["count"] += 1

        if not stats:
            return []

        # Highest commit count wins. On a tie, the smaller first_index wins
        # (earliest commit); if both first appear in the same commit, the
        # trailer that appears first breaks the tie.
        tool, entry = max(
            stats.items(),
            key=lambda item: (
                item[1]["count"],
                -item[1]["first_index"],
                -item[1]["first_line"],
            ),
        )
        return [(tool, entry["name"], entry["email"])]

    @staticmethod
    def right_replace(s, old, new, occurrence):
        """Replace {old} to {new} at most {occurrence} times from right to left."""
        li = s.rsplit(old, occurrence)
        return new.join(li)
