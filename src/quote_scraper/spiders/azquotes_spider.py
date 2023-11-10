import scrapy

class QuotesSpider(scrapy.Spider):
    name = "einstein"
    
    def start_requests(self):
        url = "https://www.azquotes.com/quotes/authors/a/"
        yield scrapy.Request(url = url, callback=self.parse_alphabet)
        

    def parse_alphabet(self, response):

        alpabeth = response.css("ul.authors a::attr(href)").getall()
        for url in alpabeth:
            yield response.follow( url = "https://www.azquotes.com" + url, callback = self.parse_pop_authors)

    def parse_pop_authors(self, response):

        authors = response.css("div.profile.most-popular a::attr(href)").getall()

        for url in authors:
            yield response.follow( url = "https://www.azquotes.com" + url, callback = self.parse_author)



    def parse_author(self, response):
        for quote in response.css("div.wrap-block"):
            yield {
                "text": quote.css('a.title::text').get(),
                "author": quote.css("a.title").attrib["data-author"],
                "tags": quote.css("div.mytags a::text").getall(),
                "likes": quote.css("a.heart24::text").getall()
            }

        next_page = response.urljoin(response.css("li.next a").attrib['href'])
        if next_page:
            yield response.follow(next_page, callback = self.parse_author)

