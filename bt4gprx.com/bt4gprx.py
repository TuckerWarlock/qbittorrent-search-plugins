# VERSION: 2.0
# AUTHORS: kjjejones44, TuckerWarlock

from html.parser import HTMLParser
from urllib.parse import urljoin
from helpers import retrieve_url, download_file
from novaprinter import prettyPrinter
import re
import json

class bt4gprx(object):
    url = "https://bt4gprx.com/"
    name = "bt4gprx"
    supported_categories = {'all': '', 'movies': 'movie/', 'tv': 'movie/', 'music': 'audio/', 'books': 'doc/', 'software': 'app/'}

    def __init__(self):
        self.trackerlist = []

    class MyHTMLParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.is_in_container = False
            self.is_in_entry = False
            self.b_value = ""
            self.container_row_count = 0
            self.temp_result = {}
            self.results = []

        def feed(self, feed: str) -> None:
            super().feed(feed)
            return self.results

        def handle_starttag(self, tag, attrs):
            attr_dict = {x[0]:x[1] for x in attrs}
            if tag == "div":
                if not self.is_in_container and attr_dict.get("class", "") == "container":
                    self.is_in_container = True
            elif tag == "a":
                if self.is_in_container and all(x in attr_dict for x in ["title", "href"]):
                    self.is_in_entry = True
                    self.temp_result.update(attr_dict)
            elif tag == "b":
                if self.is_in_entry:
                    classname = attr_dict.get("class", "")                
                    idname = attr_dict.get("id", "")
                    self.b_value = "filesize" if "cpill" in classname else idname

        def handle_endtag(self, tag):        
            if tag == "div":
                self.is_in_entry = False

        def handle_data(self, data):
            if self.b_value != "":
                self.temp_result[self.b_value] = data
                if self.b_value == "leechers":
                    self.results.append(self.temp_result)
                    self.temp_result = {}
                self.b_value = ""

    def search(self, term, cat="all"):
        pagenumber = 1
        all_results = []
        while True:
            result_page = self.search_page(term, pagenumber, cat)
            if result_page:
                all_results.extend(result_page)
            else:
                break
            pagenumber = pagenumber + 1
        self.pretty_print_results(all_results)

    def search_page(self, term, pagenumber, cat):
        try:
            query = f"{self.url}{self.supported_categories[cat]}search/{term}/byseeders/{pagenumber}"
            parser = self.MyHTMLParser()
            return parser.feed(retrieve_url(query))
        except Exception as e:
            return []

    def download_torrent(self, info):
        try:
            content = retrieve_url(info)
            match = re.search(r'href="//(downloadtorrentfile.com/hash/[^"]+)', content)
            if not match:
                print("Failed to find downloadtorrentfile.com link.")
                return
            actual_link = "https:" + match.group(0)
        except Exception as e:
            print(f"Error extracting downloadtorrentfile.com link: {e}")
            return
        try:
            hash_value = actual_link.split("/hash/")[1].split("?")[0]
            name_value = actual_link.split("?name=")[1]
        except Exception as e:
            print(f"Error extracting hash and name: {e}")
            return
        if not self.trackerlist:
            self.trackerlist = json.loads(retrieve_url("https://downloadtorrentfile.com/trackerlist"))
        magnet = f"magnet:?xt=urn:btih:{hash_value}&dn={name_value}&tr=" + "&tr=".join(self.trackerlist)
        return magnet

    def pretty_print_results(self, results):
        sorted_results = sorted(results, key=lambda x: int(x['seeders']), reverse=True)
        for result in sorted_results:
            magnet_link = self.download_torrent(urljoin(self.url, result['href']))
            temp_result = {
                'name': result['title'],
                'size': result['filesize'],
                'seeds': result['seeders'],
                'leech': result['leechers'],
                'engine_url': self.url,
                'link': magnet_link
            }
            prettyPrinter(temp_result)
