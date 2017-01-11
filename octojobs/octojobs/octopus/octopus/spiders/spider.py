"""Module for our initial spider."""
import scrapy
import re
from octopus.items import OctopusItem


class JobSpider(scrapy.Spider):
    """Job Spider which will crawl the start_urls.

    And run the parse method on each of them.
    """

    name = "jobs"

    start_urls = [
        'https://www.indeed.com/jobs?q=developer&l=seattle%2C+wa',
    ]

    def parse(self, response):
        """Default callback used by Scrapy to process downloaded responses.

        If the spider is on a home page with a list view, build a dictionary.
        This dictionary will contain references to each url, and the
        associated job title, company name, location, and summary.
        It will then use that url in its callback to the parse method, which
        lets it follow that link to what should be a detail view. As of this
        commit, all data is saved in a unique file as JSON.

        Once the spider is on a detail view, it captures the CSS/ xPath
        selectors for the data we want to port to our database. The spider then
        returns to the home view and runs parse() again.

        Once the spider reaches the end of the urls on the page, it will follow
        the link to the next page of results.
        """
        items = {}
        company_dict = {}
        if not response.xpath('//*[@id="job-content"]'):
            if response.xpath('//*[@id="resultsCol"]'):

                for element in response.css('div.result h2.jobtitle'):
                    anchor = element.css('a.turnstileLink').extract_first()
                    title = re.search(r'title="([^"]*)"', anchor).group(1)

                    base_url = 'https://www.indeed.com'
                    url = base_url + re.search(
                        r'href="([^"]*)"', anchor).group(1)
                    company_dict[url] = {}
                    company_dict[url]['url'] = url
                    company_dict[url]['title'] = title

                    data = response.css('div.result span.company')
                    if data.css('span a'):
                        company = data.css('span a::text').extract_first()
                    else:
                        company = data.css('span::text').extract_first()
                    company = ' '.join(company.split())
                    company_dict[url]['company'] = company

                    location = response.css(
                        'div.result span.location::text').extract_first()
                    company_dict[url]['city'] = location

                    summary = response.css(
                        'div.result span.summary::text').extract_first()
                    company_dict[url]['description'] = summary

                for key in company_dict:
                    yield scrapy.Request(key)

                    if not response.xpath('//*[@id="job-content"]'):
                        items[key] = OctopusItem(
                            title=company_dict[key]['title'],
                            url=company_dict[key]['url'],
                            company=company_dict[key]['company'],
                            city=company_dict[key]['city'],
                            description=company_dict[key]['description'],
                        )
                        continue

            elif response.xpath('//*[@id="job-content"]'):
                for job in response.xpath('//*[@id="job-content"]'):
                    items[response.url] = OctopusItem(
                        title=job.css('font::text').extract_first(),
                        url=response.url,
                        company=job.css(
                            'span.company::text').extract_first(),
                        city=job.css(
                            'span.location::text').extract_first(),
                        description=job.css(
                            'span.summary::text').extract_first(),
                    )

        next_page = response.css(
            'div.pagination a::attr(href)').extract_first()
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parse)
        yield items
