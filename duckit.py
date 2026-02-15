#!/usr/bin/env python3
import argparse, json, os, re
from html.parser import HTMLParser
from urllib.error import HTTPError
from urllib.parse import quote, unquote, urlparse, parse_qs, urlencode
from urllib.request import Request, urlopen

DEFAULT_USER_AGENT = 'Mozilla/5.0'
searchURL = 'https://html.duckduckgo.com/html/?q='

class DDGParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_results = False
        self.in_result_body = False
        self.in_title = False
        self.in_snippet = False

        self.current = {}
        self.results = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        # Start of results container
        if tag == "div" and attrs.get("id") == "links":
            self.in_results = True

        # Start of a result body
        if self.in_results and tag == "div":
            cls = attrs.get("class", "")
            if "result__body" in cls:
                self.in_result_body = True
                self.current = {}

        # Title link
        if self.in_result_body and tag == "a":
            cls = attrs.get("class", "")
            if "result__a" in cls:
                self.in_title = True
                self.current["link"] = self._parse_ddg_link(attrs.get("href", ""))

        # Snippet link
        if self.in_result_body and tag == "a":
            cls = attrs.get("class", "")
            if "result__snippet" in cls:
                self.in_snippet = True

    def handle_endtag(self, tag):
        if tag == "div" and self.in_result_body:
            # End of a result block
            if self.current:
                self.results.append(self.current)
            self.in_result_body = False

        if tag == "a":
            self.in_title = False
            self.in_snippet = False

    def handle_data(self, data):
        if self.in_title:
            self.current["title"] = data.strip()
        if self.in_snippet:
            self.current["snippet"] = data.strip()

    def _parse_ddg_link(self, href):
        # Extract uddg= URL
        url = urlparse(href)
        qs = parse_qs(url.query)
        if "uddg" in qs:
            return unquote(qs["uddg"][0])
        return href

class DuckIt:
    def __init__(self):
        self.offset = 0
        self.parser = DDGParser()
        self.query = None
        self.vqd = None

    def page(self, cmd):
        if not self.vqd or not self.query:
            print("No active search")
            return []

        if cmd == 'n':
            self.offset += 10
        elif cmd == 'p':
            self.offset = max(0, self.offset - 10)
        else:
            try:
                page = int(cmd)
                self.offset = (page - 1) * 10
            except ValueError:
                print("Invalid page command")
                return []

        data = urlencode({
            "q": self.query,
            "s": str(self.offset),
            "vqd": self.vqd,
        }).encode()

        response = self.request("https://html.duckduckgo.com/html/", data=data)
        if not response:
            return []

        html = response.read().decode("utf-8", errors="ignore")

        # parse results
        self.parser = DDGParser()
        self.parser.feed(html)
        return self.parser.results

    def request(self, url, data=None):
        req = Request(url, data=data, headers={'User-Agent': DEFAULT_USER_AGENT})
        try:
            return urlopen(req)
        except HTTPError as e:
            print("HTTP error:", e.code, e.msg)
            return None

    def search(self, query):
        self.offset = 0
        self.query = ' '.join(query)
        q = quote(self.query)

        response = self.request(f"{searchURL}{q}")
        if not response:
            return []

        html = response.read().decode("utf-8", errors="ignore")

        # extract vqd
        m = re.search(r'name="vqd" value="([^"]+)"', html)
        self.vqd = m.group(1) if m else None

        # parse results
        self.parser = DDGParser()
        self.parser.feed(html)
        return self.parser.results

def repl():
    duck = DuckIt()
    print("DuckIt REPL — type 'help' for commands, 'quit' to exit")
    print("Commands:")
    print("  /query text     perform a search")
    print("  n               next page")
    print("  p               previous page")
    print("  <number>        jump to page number")

    while True:
        try:
            line = input("> ").strip()
        except EOFError:
            break

        if not line:
            continue

        if line in ("quit", "exit"):
            break

        if line == "help":
            print("Commands:")
            print("  /query text     perform a search")
            print("  n               next page")
            print("  p               previous page")
            print("  <number>        jump to page number")
            continue

        if line.startswith("/"):
            query = line[1:].strip().split()
            duck.search(query)
        else:
            duck.page(line)
        
        results(duck)        
        
def results(duck):
    for r in duck.parser.results: 
        domain = urlparse(r.get("link", "")).netloc 
        print(f"[{domain}] {r.get('title', '(no title)')}") 
        print(f"{r.get('snippet', '(no snippet)')}") 
        print(f"URL: {r.get('link', '(no link)')}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Minimal DuckDuckGo HTML scraper")
    parser.add_argument("query", nargs="*", help="Search terms")
    args = parser.parse_args()

    if not args.query:
        repl()
    else:
        duck = DuckIt()
        duck.search(args.query)
        results(duck)
