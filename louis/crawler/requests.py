from urllib.parse import urlparse
import scrapy

def extract_urls(response, parse):
    for href in response.xpath("//a/@href").getall():
        if href.endswith('pdf'):
            continue
        # remove anchors and query params urls
        href = href.split('#')[0]
        href = href.split('?')[0]
        if href.startswith('http'):
            pass
        elif href.startswith('/'):
            # add relative url to full domain
            parsed = urlparse(response.url)
            href = parsed.scheme + "://" + parsed.netloc + href
        else:
            continue
        href = fix_vhost(href)
        yield scrapy.Request(href, parse, headers={'Referer': response.url})

def fix_vhost(url):
    url = url.replace('https://inspection.gc.ca', 'http://inspection.canada.ca')
    url = url.replace('https://www.inspection.gc.ca', 'http://inspection.canada.ca')
    return url