# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

# useful for handling different item types with a single interface
from scrapy import signals


class QuoteScraperSpiderMiddleware:
    """
    Spider middleware which is responsible for processing inputs and outputs of the spider.
    """

    @classmethod
    def from_crawler(cls, crawler):
        """
        Create an instance of the middleware for the spider.

        :param crawler: The Scrapy crawler.
        :return: Instance of the middleware.
        """
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):  # pylint: disable=unused-argument
        """
        Process spider input.
        Called for each response that goes through the spider middleware and into the spider.

        :param response: The response object.
        :param spider: The spider instance.
        :return: None or raise an exception.
        """
        return None

    def process_spider_output(self, response, result, spider):  # pylint: disable=unused-argument
        """
        Process spider output which is called with the results returned from the Spider,
        after it has processed the response.

        :param response: The response object.
        :param result: The result returned by the spider.
        :param spider: The spider instance.
        :return: Iterable of Request or item objects.
        """
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):  # pylint: disable=unused-argument
        """
        Process spider exception executed when a spider or process_spider_input()
        method raises an exception.

        :param response: The response object.
        :param exception: The exception raised.
        :param spider: The spider instance.
        :return: None or an iterable of Request or item objects.
        """

    def process_start_requests(self, start_requests, spider):  # pylint: disable=unused-argument
        """
        Process start requests. Called with the start requests of the spider.

        :param start_requests: The start requests of the spider.
        :param spider: The spider instance.
        :return: Only requests (not items).
        """
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        """
        Log spider opening.
        :param spider: The spider instance.
        """
        spider.logger.info(f"Spider opened: {spider.name}")


class QuoteScraperDownloaderMiddleware:
    """
    This middleware is responsible for processing requests, responses, and exceptions during download.
    """

    @classmethod
    def from_crawler(cls, crawler):
        """
        Create an instance of the downloader middleware for the spider.

        :param crawler: The Scrapy crawler.
        :return: Instance of the downloader middleware.
        """
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):  # pylint: disable=unused-argument
        """
        Called for each request that goes through the downloader middleware.

        :param request: The request object.
        :param spider: The spider instance.
        :return: None to continue processing this request, a Response object, a Request object, or raise IgnoreRequest.
        """
        return None

    def process_response(self, request, response, spider):  # pylint: disable=unused-argument
        """
        Responding the response returned from the downloader.

        :param request: The request object.
        :param response: The response object.
        :param spider: The spider instance.
        :return: A Response object, a Request object, or raise IgnoreRequest.
        """
        return response

    def process_exception(self, request, exception, spider):  # pylint: disable=unused-argument
        """
        Executed when a download handler or a process_request() raises an exception.

        :param request: The request object.
        :param exception: The exception raised.
        :param spider: The spider instance.
        :return: None to continue processing this exception, a Response object to stop the process_exception() chain,
                 a Request object to stop the process_exception() chain.
        """

    def spider_opened(self, spider):
        """
        Called when the spider is opened.

        :param spider: The spider instance.
        """
        spider.logger.info(f"Spider opened: {spider.name}")
