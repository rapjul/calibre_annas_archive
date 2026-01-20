try:
    from calibre.customize import StoreBase  # type: ignore  # type: ignore
except ImportError:

    class StoreBase:  # type: ignore
        ...


class AnnasArchiveStore(StoreBase):  # type: ignore
    name: str = "Anna's Archive"
    description: str = "The world's largest open-source open-data library."
    supported_platforms: list[str] = ["windows", "osx", "linux"]
    author: str = "ScottBot10"
    version: tuple[int, int, int] = (0, 3, 0)
    minimum_calibre_version: tuple[int, int, int] = (5, 0, 0)
    formats: list[str] = [
        "EPUB",
        "MOBI",
        "PDF",
        "AZW3",
        "CBR",
        "CBZ",
        "FB2",
    ]
    drm_free_only: bool = True

    actual_plugin = "calibre_plugins.store_annas_archive.annas_archive:AnnasArchiveStore"

    def is_customizable(self):
        return True

    def customization_help(self, gui=False):
        return "Enter your Anna's Archive configuration."

    def config_widget(self):
        from calibre.utils.config import JSONConfig
        from calibre_plugins.store_annas_archive.config import ConfigWidget

        self.config = JSONConfig("plugins/store_annas_archive")
        return ConfigWidget(self)

    def save_settings(self, config_widget):
        config_widget.save_settings()
