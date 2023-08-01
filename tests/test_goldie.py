import unittest

from scrapy import Request
from bs4 import BeautifulSoup
from louis.crawler.responses import fake_response_from_file
from louis.crawler.spiders.goldie import GoldieSpider

# get directory of this file
# https://stackoverflow.com/questions/5137497/find-current-directory-and-files-directory'
import os

cwd = os.path.dirname(os.path.abspath(__file__))


def get_response(url):
    filename = url.split("/")[-1]
    return fake_response_from_file(f"{cwd}/responses/{filename}.html", url=url)


class TestGoldie(unittest.TestCase):
    def setUp(self):
        self.spider = GoldieSpider()

    def _test_item_results(self, results, expected_length):
        returned_results = []
        for item in results:
            if isinstance(item, Request):
                # probably a Request object for additional processing
                continue
            self.assertIsNotNone(item["url"])
            returned_results.append(item)
        self.assertEqual(len(returned_results), expected_length)
        return returned_results

    def test_sample1(self):
        url = "https://inspection.canada.ca/inspection-and-enforcement/enforcement-of-the-sfcr/eng/1546989322632/1547741756885"
        response = get_response(url)

        results = self.spider.parse(response)
        results = self._test_item_results(results, 1)
        self.assertEqual(
            results[0]["title"],
            "Enforcement of the Safe Food for Canadians Regulations - Canadian Food Inspection Agency",
        )
        self.assertEqual(results[0]["url"], url)
        self.assertTrue(
            results[0]["html_content"].startswith(
                '<html><body><main class="container" property="mainContentOfPage" typeof="WebPageElement"> <h1 id="wb-cont" property="name">Enforcement of the <i>Safe Food for Canadians Regulations</i>'
            )
        )

    def test_sample2(self):
        url = "https://inspection.canada.ca/food-safety-for-industry/toolkit-for-food-businesses/understanding-the-sfcr/eng/1492029195746/1492029286734"
        response = get_response(url)
        results = self.spider.parse(response)
        results = self._test_item_results(results, 1)

    def test_sample_organization_structure(self):
        url = "https://inspection.canada.ca/about-cfia/organizational-structure/eng/1323224617636/1323224814073"
        response = get_response(url)
        results = self.spider.parse(response)
        results = self._test_item_results(results, 1)
        html_content = results[0]["html_content"]
        soup = BeautifulSoup(html_content, "html.parser")
        text_content = [s for s in soup.stripped_strings]
        print(text_content)
        self.assertEqual(
            text_content,
            [
                "Organizational structure",
                "The Canadian Food Inspection Agency (CFIA) is led by its President, who reports to the Minister of Health. The CFIA has an integrated governance structure whereby all branch heads have specific accountabilities that contribute to the achievement of each of the CFIA's strategic objectives.",
                "President",
                "Executive Vice-President",
                "Chief officers",
                "Chief Veterinary Officer and Delegate to the World Organisation for Animal Health",
                "Chief Food Safety Officer",
                "Chief Plant Health Officer",
                "Chief Science Operating Officer and Science Integrity Lead",
                "Chief Scientific Data Officer",
                "Senior management structure",
                "Ministerial mandate letters",
                "Minister of Health mandate letter",
                "Minister of Agriculture and Agri-Food mandate letter",
                "Minister of Innovation, Science and Economic Development mandate letter",
            ],
        )


if __name__ == "__main__":
    unittest.main()
