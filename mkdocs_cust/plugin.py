from mkdocs import plugins
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin

import logging
from mkdocs_cust.util import add_target_blank_to_links


logger = logging.getLogger("mkdocs.plugins.mkdocs-cust")


class CustPlugin(BasePlugin):
    config_scheme = (
        ("external_link_target_blank", config_options.Type(bool, default=True)),
    )

    @plugins.event_priority(50)
    def on_page_content(self, html, *, page, config, files):
        if self.config["external_link_target_blank"]:
            html = add_target_blank_to_links(html)
        return html
