from __future__ import annotations

import json
import time
from contextlib import closing
from http.client import RemoteDisconnected
from math import ceil
from typing import Any, Generator
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

_LAST_ALL_MIRRORS_DOWN_TIME: float = 0.0

try:
    from calibre import browser  # pyright: ignore[reportMissingImports]
    from calibre.gui2 import open_url  # pyright: ignore[reportMissingImports]
    from calibre.gui2.store import StorePlugin  # pyright: ignore[reportMissingImports]
    from calibre.gui2.store.search_result import SearchResult  # pyright: ignore[reportMissingImports]
    from calibre.gui2.store.web_store_dialog import WebStoreDialog  # pyright: ignore[reportMissingImports]
except ImportError:
    # Mocks for linting/type checking when calibre is not installed
    def browser() -> Any: ...
    def open_url(url: Any) -> None: ...

    class StorePlugin:
        def __init__(self, gui: Any, name: str, config: Any = None, base_plugin: Any = None) -> None: ...

    class SearchResult:
        DRM_UNLOCKED: str = "unlocked"

        def __init__(self) -> None:
            self.detail_item: str = ""
            self.cover_url: str = ""
            self.title: str = ""
            self.author: str = ""
            self.formats: str = ""
            self.price: str = ""
            self.drm: str = ""
            self.downloads: dict[str, str] = {}

    class WebStoreDialog:
        def __init__(self, gui: Any, base: str, parent: Any, url: str) -> None: ...
        def setWindowTitle(self, title: str) -> None: ...
        def set_tags(self, tags: str) -> None: ...
        def exec(self) -> None: ...


from calibre_plugins.store_annas_archive.constants import DEFAULT_MIRRORS, RESULTS_PER_PAGE, SearchOption
from lxml import html

try:
    from qt.core import QUrl
except (ImportError, ModuleNotFoundError):
    try:
        from PyQt6.QtCore import QUrl
    except (ImportError, ModuleNotFoundError):
        from PyQt5.QtCore import QUrl

SearchResults = Generator[SearchResult, None, None]


class AnnasArchiveStore(StorePlugin):
    def __init__(self, gui: Any, name: str, config: dict[str, Any] | None = None, base_plugin: Any = None) -> None:
        super().__init__(gui, name, config, base_plugin)
        self.working_mirror = None

    def _search(self, url: str, max_results: int, timeout: int) -> SearchResults:
        global _LAST_ALL_MIRRORS_DOWN_TIME
        if self.config.get("circuit_breaker", False) and (time.time() - _LAST_ALL_MIRRORS_DOWN_TIME < 300):
            raise Exception("All of your Anna's Archive mirrors are down. Circuit breaker active for 5 minutes.")

        br = browser()
        doc: Any = None
        counter = max_results

        for page in range(1, ceil(max_results / RESULTS_PER_PAGE) + 1):
            mirrors = list(self.config.get("mirrors", DEFAULT_MIRRORS))
            if self.working_mirror and self.working_mirror in mirrors:
                mirrors.remove(self.working_mirror)
                mirrors.insert(0, self.working_mirror)
            for mirror in mirrors:
                try:
                    with closing(br.open(url.format(base=mirror, page=page), timeout=timeout)) as resp:
                        if resp.code < 500 or resp.code > 599:
                            self.working_mirror = mirror
                            content = resp.read()
                            doc = html.fromstring(content)
                            break
                except Exception as e:
                    # Try next mirror
                    print(f"Failed to connect to {mirror}: {e}")
                    pass
            if doc is None:
                self.working_mirror = None
                if self.config.get("circuit_breaker", False):
                    _LAST_ALL_MIRRORS_DOWN_TIME = time.time()
                raise Exception(
                    "All of your Anna's Archive mirrors are unreachable. Please check your internet connection or update the mirror list in the plugin configuration (Preferences -> Plugins -> Get books -> Anna's Archive -> Customize)."
                )

            # New layout uses divs, not table rows
            books: list[Any] = doc.xpath('//a[contains(@class, "js-vim-focus")]')
            if not books:
                # Fallback or empty result
                pass

            for book in books:
                if counter <= 0:
                    break

                # The anchor with 'js-vim-focus' is inside a td, which is inside a tr
                # Structure: tr > td > a.js-vim-focus
                try:
                    tr = book.getparent().getparent()
                except AttributeError:
                    continue

                s = SearchResult()
                s.detail_item = book.get("href", "").split("/")[-1]
                if not s.detail_item:
                    continue

                try:
                    # Title is in the 2nd td (index 1)
                    # Use xpath to find all text within the cell to be safe
                    s.title = "".join(tr.xpath("./td[2]//text()")).strip()

                    # Author is in the 3rd td (index 2)
                    s.author = "".join(tr.xpath("./td[3]//text()")).strip()
                    if not s.author:
                        s.author = "Unknown"

                    # Format is in the 10th td (index 9)
                    # "pdf", "epub", etc.
                    s.formats = "".join(tr.xpath("./td[10]//text()")).strip().upper()
                    if not s.formats:
                        s.formats = "UNKNOWN"

                    # Cover image
                    # In the 1st td (index 0), inside a hidden div that appears on hover/focus
                    # <div id="hover_cover..."><img src="..."></div>
                    cover_src = tr.xpath("./td[1]//img/@src")
                    # The first img might be the small cover or the large hover one.
                    # Usually there are two images in the first td.
                    s.cover_url = cover_src[0] if cover_src else ""

                except IndexError:
                    # If table structure is different (e.g. mobile view or change), fail gracefully for this item
                    continue

                s.price = "$0.00"
                s.drm = SearchResult.DRM_UNLOCKED

                counter -= 1
                yield s

    def search(self, query: str, max_results: int = 10, timeout: int = 60) -> SearchResults:
        url = f"{{base}}/search?page={{page}}&q={quote_plus(query)}&display=table"
        search_opts = self.config.get("search", {})
        for option in SearchOption.options:
            value = search_opts.get(option.config_option, ())
            if isinstance(value, str):
                value = (value,)
            for item in value:
                url += f"&{option.url_param}={item}"
        yield from self._search(url, max_results, timeout)

    def open(self, parent: Any = None, detail_item: str | None = None, external: bool = False) -> None:
        if detail_item:
            url = self._get_url(detail_item)
        elif self.working_mirror is not None:
            url = self.working_mirror
        else:
            url = self.config.get("mirrors", DEFAULT_MIRRORS)[0]
        if external or self.config.get("open_external", False):
            open_url(QUrl(url))
        else:
            try:
                d = WebStoreDialog(self.gui, self.working_mirror, parent, url)
                d.setWindowTitle(self.name)
                d.set_tags(self.config.get("tags", ""))
                d.exec()
            except Exception:
                # WebStoreDialog doesn't work, at least not on my device
                open_url(QUrl(url))

    def get_details(self, search_result: SearchResult, timeout: int = 60) -> None:
        if not search_result.formats:
            return

        _format = "." + search_result.formats.lower()

        if self.config.get("secret"):
            resp = urlopen(self._get_url_premium(search_result.detail_item), timeout=timeout).read().decode("utf-8")
            url = json.loads(resp).get("download_url")

            if url:
                search_result.downloads[f"premium.{search_result.formats}"] = url

        br = browser()
        with closing(br.open(self._get_url(search_result.detail_item), timeout=timeout)) as f:
            doc = html.fromstring(f.read())

        for link in doc.xpath(
            '//div[@id="md5-panel-downloads"]/ul[contains(@class, "list-inside")]/li/a[contains(@class, "js-download-link")]'
        ):
            url = link.get("href")
            link_text = "".join(link.itertext())

            if "Fast Partner Server" in link_text and not self.config.get("secret"):
                continue

            try:
                if link_text == "Libgen.li":
                    # Cloudflare "Phishing Warning" popups make this impossible for us
                    continue
                elif link_text == "Libgen.rs Fiction" or link_text == "Libgen.rs Non-Fiction":
                    url = self._get_libgen_link(url, br)
                elif link_text.startswith("Sci-Hub"):
                    url = self._get_scihub_link(url, br)
                elif link_text == "Z-Library":
                    url = self._get_zlib_link(url, br)
                else:
                    continue
            except (OSError, URLError, HTTPError, TimeoutError, RemoteDisconnected) as e:
                br.set_handle_gzip(False)  # Reset potentially messed up browser state
                print(f"Failed to resolve link '{link_text}': {e}")
                continue

            if not url:
                continue

            # Takes longer, but more accurate
            # Get rid of extension checking because basically none have extensions...
            try:
                # Because Z-Lib downloads use hashes, we can't check them :(
                if "z-lib" not in url:
                    with urlopen(Request(url, method="HEAD"), timeout=timeout) as resp:
                        if resp.info().get_content_maintype() != "application":
                            continue
            except (HTTPError, URLError, TimeoutError, RemoteDisconnected):
                pass
            search_result.downloads[f"{link_text}.{search_result.formats}"] = url

    @staticmethod
    def _get_libgen_link(url: str, br: Any) -> str:
        with closing(br.open(url)) as resp:
            doc = html.fromstring(resp.read())
        # Fiction
        url = "".join(doc.xpath('//ul[contains(@class, "record_mirrors")]/li[1]/a/@href'))

        # Handle non-fiction
        if not url:
            url = "".join(doc.xpath('//a[@title="Libgen & IPFS & Tor"]/@href'))
        # Replace http with https because it doesn't work without it
        url = url.replace("http", "https")

        # Open the new books.ms url and look for the 'get' button there
        with closing(br.open(url)) as resp:
            doc = html.fromstring(resp.read())
            scheme, _, host, _ = resp.geturl().split("/", 3)
        url = "".join(doc.xpath('//div[@id="download"]/h2[1]/a/@href'))
        return url

    @staticmethod
    def _get_libgen_nonfiction_link(url: str, br) -> str:
        with closing(br.open(url)) as resp:
            doc = html.fromstring(resp.read())
        url = "".join(doc.xpath('//h2/a[text()="GET"]/@href'))
        return url

    @staticmethod
    def _get_scihub_link(url: str, br: Any) -> str | None:
        with closing(br.open(url)) as resp:
            doc = html.fromstring(resp.read())
            scheme, _ = resp.geturl().split("/", 1)
        url = "".join(doc.xpath('//embed[@id="pdf"]/@src'))
        if url:
            return scheme + url

    # With Z-Lib, every download has a hash
    @staticmethod
    def _get_zlib_link(url: str, br: Any) -> str | None:
        with closing(br.open(url)) as resp:
            doc = html.fromstring(resp.read())
            scheme, _, host, _ = resp.geturl().split("/", 3)
        url = "".join(doc.xpath('//a[contains(@class, "addDownloadedBook")]/@href'))
        if url:
            # The url already has a leading /
            return f"{scheme}//{host}{url}"

    def _get_url(self, md5: str) -> str:
        return f"{self.working_mirror}/md5/{md5}"

    def _get_url_premium(self, md5: str) -> str:
        secret = self.config.get("secret")
        return f"{self.working_mirror}/dyn/api/fast_download.json?md5={md5}&key={secret}"

    def config_widget(self) -> Any:
        from calibre_plugins.store_annas_archive.config import ConfigWidget

        return ConfigWidget(self)

    def save_settings(self, config_widget: Any) -> None:
        config_widget.save_settings()
