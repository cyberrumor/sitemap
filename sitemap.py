#!/usr/bin/env python3
from __future__ import annotations 
# from time import sleep
import sys
import os
import requests
from bs4 import BeautifulSoup
import urllib
import logging

class Page:
    """This class represents a page on a website, the pages it links to, the pages that link to it, the website it was found on, and whether it was scanned."""
    def __init__(self, 
            website: str | Page,
            url: str, 
            session: requests.Session,
            blacklist: List[Page] = []):

        self.website: str | Page = website
        self.url = urllib.parse.urlparse(url)
        self.session = session
        self.children = []
        self.parents = []
        self.scanned = False
        self.blacklist = blacklist
        self.status_code = "Skipped."

    def __len__(self) -> int:
        """len should return the number of this page's immediate children."""
        return len(self.children)

    def get_page(self, href: str | urllib.parse.ParseResult) -> Page:
        """Returns existing page if href exists, otherwise creates and returns a new page instance."""
        match href:
            case str():
                for p in self.website.children:
                    if p.url.geturl() == href:
                        return p
                # the page is unique
                p = Page(self.website, href, self.website.session, self.website.blacklist)
                return self.domain_test(p)

            case urllib.parse.ParseResult():
                for p in self.website.children:
                    if p.url.geturl() == href.geturl():
                        return p
                # the page is unique
                p = Page(self.website, href.geturl(), self.session, self.website.blacklist)
                return self.domain_test(p)
            case _:
                raise TypeError(f"expected str or urllib.parse.ParseResult as argument type. Got {type(href)}.")

    def domain_test(self, page: Page) -> Page:
        """Guarantee we stay on the same domain, and ensure we have absolute paths for our urls."""
        if page.url[1] != self.website.url[1]:

            if page.url[1] == '':
                # the href's netloc was an empty string.
                # Create a full url, parsed, by url joining target website and href.
                page.url = urllib.parse.urlparse(
                        urllib.parse.urljoin(
                            self.website.url.geturl(),
                            page.url.geturl()
                        ))

            else:
                # href's netloc wasn't an empty string, AND it was on a different domain than the target.
                # Skip scanning by marking it as scanned.
                page.scanned = True
        return page

    def get_urls(self):
        """Get a list of all links found on this page."""
        # return structure is like so:
        # [("http://127.0.0.1", 200), ("http://127.0.0.1/not_found", 404), ("http://192.168.1.11", "Skipped"), ...]
        return [(i.url.geturl(), i.status_code) for i in self.children]

    def get_parent_urls(self):
        """Get a list of all pages that refernce this one."""
        # return structure is like so:
        # [("http://127.0.0.1", 200), ("http://127.0.0.1/not_found", 404), ("http://192.168.1.11", "Skipped"), ...]
        return [(i.url.geturl(), i.status_code) for i in self.parents]

    def add_child(self, href) -> None:
        """Track when this page links to another."""
        match href:
            case str():
                p = self.get_page(href)
                if p not in self.children:
                    self.children.add(p)
            case Page():
                if href not in self.children:
                    self.children.append(href)
            case urllib.parse.ParseResult():
                p = self.get_page(href)
                if p not in self.children:
                    self.children.append(p)
            case _:
                raise TypeError(f'Expected str or Page, got {type(href)}')

    def add_parent(self, href) -> None:
        """Track when this page was referenced by another."""
        match href:
            case str():
                p = self.get_page(href)
                if p not in self.parents:
                    self.parents.append(p)
            case Page():
                if href not in self.parents:
                    self.parents.append(href)
            case urllib.parse.ParseResult():
                p = self.get_page(href)
                if p not in self.parents:
                    self.parents.append(p)
            case _:
                raise TypeError(f'Expected str or Page, got {type(href)}')

    def scan(self) -> None:
        """Collect all child hrefs and form action pages."""
        self.scanned = True
        # don't scan urls with blacklisted words.
        for word in self.blacklist:
            if word.lower() in self.url.geturl().lower():
                return
        try:
            r = self.session.get(self.url.geturl())
            self.status_code = r.status_code
            if r.status_code:
                soup = BeautifulSoup(r.text, 'html.parser')
                # get hrefs
                for a in soup.find_all('a'):
                    href = a.get('href')
                    if href:
                        p = self.get_page(href)
                        p.add_parent(self.url)
                        self.add_child(p)
                        self.website.add_child(p)

        except Exception as e:
            """I need to handle each type of exception explicitly so I can determine
            whether to skip, add to rate limit, retry, etc.
            https://requests.readthedocs.io/en/latest/api/#exceptions
            """
            logging.error(f'Error while scanning {self.url.geturl()}, skipping.')
            logging.error(f'The error produced was {e}')


class App:
    """This is a handler class that will scan a single domain.
    Create multiple instances of this class and call .run() on each to scan multiple different domains.
    """
    def __init__(self, blacklist: List[str], target: str):
        self.blacklist = blacklist
        self.target = target
        self.session = requests.Session()
        self.website = None

    def run(self) -> None:
        """Create our website instance and initiate a scan."""
        website = Page(self.target,
                self.target,
                self.session,
                self.blacklist)

        # refactor our class so we don't have to doctor our first instance right after creation.
        website.website = website
        website.scan()
        self.website = website
        logging.info(f'\t{website.url.geturl():<70} {website.status_code}')

        # scan and add pages until they are all scanned.
        while not all([i.scanned for i in website.children]):
            for page in [i for i in website.children if not i.scanned]:
                page.scan()

        # print our website list.
        for i in website.get_urls():
            logging.info(f'\t{i[0]:<70} {i[1]}')

        print()


if __name__ == '__main__':
    """__main__ handles normal CLI usage and can serve as an example of how to run this file as an import."""
    if len(sys.argv) == 1:
        print(f'Usage: python3 {__file__.rsplit("/")[-1]} mp4 png http://127.0.0.1')
        exit()

    # initialize our logging preferences.
    logging.basicConfig(level = logging.INFO, format = '%(asctime)s:%(levelname)s:%(message)s')

    blacklist = sys.argv[1:-1]
    target = sys.argv[-1]
    app = App(blacklist, target)
    app.run()

    """
    # show all children of our website
    for page in app.website.get_urls():
        print(f'{page[0]:<70} {page[1]}')


    print()
    # show all pages that reference our third link
    for page in app.website.children[2].get_parent_urls():
        print(page)
    """



