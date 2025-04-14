from mkdocs import plugins
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from mkdocs.structure.toc import get_toc
from mkdocs.structure.files import File, Files

import logging
import os

from mkdocs_cust.util import (
    add_target_blank_to_links,
    ipynb_to_html,
    get_toc_tokens,
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


class CustPlugin(BasePlugin):
    config_scheme = (
        ("external_link_target_blank", config_options.Type(bool, default=True)),
        ("convert_ipynb", config_options.Type(bool, default=True)),
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
