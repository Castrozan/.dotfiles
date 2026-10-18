from agent_api.contract import CapabilityError, validate_url


class CrawlingProvider:
    def preflight(self, request):
        from cssselect import HTMLTranslator, SelectorError
        from parsel import Selector

        validate_url(request.input["url"])
        extraction = request.input.get("extraction")
        if extraction is None:
            return
        selector = Selector(text="<html><body></body></html>")
        try:
            HTMLTranslator().css_to_xpath(extraction["item_selector"])
            for expression in extraction["fields"].values():
                selector.css(expression)
        except (SelectorError, ValueError, TypeError):
            raise CapabilityError("invalid_selector") from None

    def execute(self, request, directory, operation_id):
        from scrapy import signals
        from scrapy.crawler import CrawlerProcess

        from agent_api.providers.site_spider import OriginMiddleware, SiteSpider

        process = CrawlerProcess(
            settings={
                "USER_AGENT": "agent-api/1.0 (Scrapy; programmatic site extraction)",
                "ROBOTSTXT_OBEY": True,
                "CONCURRENT_REQUESTS": 1,
                "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
                "DOWNLOAD_DELAY": 0.25,
                "RANDOMIZE_DOWNLOAD_DELAY": False,
                "DOWNLOAD_TIMEOUT": min(30, request.timeout_seconds),
                "DOWNLOAD_MAXSIZE": 1024 * 1024,
                "DOWNLOAD_WARNSIZE": 1024 * 1024,
                "DOWNLOADER_CLIENTCONTEXTFACTORY": "scrapy.core.downloader.contextfactory.BrowserLikeContextFactory",
                "DOWNLOADER_MIDDLEWARES": {OriginMiddleware: 50},
                "REDIRECT_MAX_TIMES": 5,
                "METAREFRESH_ENABLED": False,
                "RETRY_ENABLED": False,
                "COOKIES_ENABLED": False,
                "HTTPPROXY_ENABLED": False,
                "TELNETCONSOLE_ENABLED": False,
                "LOG_ENABLED": False,
                "LOGSTATS_INTERVAL": 0,
                "DNS_TIMEOUT": min(10, request.timeout_seconds),
                "REACTOR_THREADPOOL_MAXSIZE": 2,
                "DEPTH_PRIORITY": 1,
                "SCHEDULER_MEMORY_QUEUE": "scrapy.squeues.FifoMemoryQueue",
            },
            install_root_handler=False,
        )
        crawler = process.create_crawler(SiteSpider)
        failures = []
        crawler.signals.connect(
            lambda failure, **values: failures.append(failure),
            signal=signals.spider_error,
            weak=False,
        )
        pending = process.crawl(crawler, parameters=request.input, directory=directory)
        pending.addErrback(lambda failure: failures.append(failure))
        process.start(install_signal_handlers=False)
        if failures:
            raise CapabilityError("crawl_failed")
        spider = crawler.spider
        if spider is None or not spider.pages:
            raise CapabilityError("crawl_empty")
        return {
            "artifact": "crawl.jsonl",
            "pages": spider.pages,
            "errors": spider.errors,
            "scheduled_pages": len(spider.scheduled_urls),
            "finish_reason": crawler.stats.get_value("finish_reason"),
            "javascript_rendered": False,
        }
