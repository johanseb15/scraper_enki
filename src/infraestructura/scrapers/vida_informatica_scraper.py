class VidaInformaticaScraper(BaseScraper):
    def __init__(self, downloader=None, **kwargs):
        self.downloader = downloader or DefaultDownloader()