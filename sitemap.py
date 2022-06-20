#!/usr/bin/env python3
# from time import sleep
import sys
import os
import requests
from bs4 import BeautifulSoup
import urllib
import logging

class Page:

    def __init__(self, website, url, session, blacklist = None):
        self.website = website # we generally want self.website to all be the same id(website) as other Page instances.
        self.url = urllib.parse.urlparse(url) # we are going to parse here to help us identify domains.
        self.session = session # this should generally be the same id(session) as the other Page instances.
        self.children = set(()) # ignore duplicates and order doesn't matter.
        self.parents = set(()) # ignore duplicates and order doesn't matter.
        self.scanned = False # we will use this to track whether a page has been scanned, but also to track pages to skip (due to differing domains)
        self.blacklist = blacklist # same for blacklist.
        self.status_code = "Skipped."

    # len(Page) should return number of immediate children.
    def __len__(self) -> int:
        return len(self.children)

    # accepts str, or urllib.parse.ParseResult.
    # returns existing Page if possible, otherwise new Page.
    def get_page(self, href):
        match href:
            case str():
                for p in self.website.children:
                    if p.url.geturl() == href:
                        return p
                # the page is unique
                p = Page(self.website, href, self.website.session, self.website.blacklist)
                # don't scan out of scope domains.
                return self.domain_test(p)

            case urllib.parse.ParseResult():
                for p in self.website.children:
                    if p.url.geturl() == href.geturl():
                        return p
                # the page is unique
                p = Page(self.website, href.geturl(), self.session, self.website.blacklist)
                # don't scan out of scope domains.
                return self.domain_test(p)

    # guarantee we stay on the same domain. Don't scan off domain sites, and urljoin the target with the url if the netloc was an empty string.
    def domain_test(self, page):
        if page.url[1] != self.website.url[1]:

            if page.url[1] == '':
                # the href's netloc was an empty string.
                # Create a full url, parsed, by url joining target website and href.
                page.url = urllib.parse.urlparse(
                        urllib.parse.urljoin(
                            self.website.url.geturl(),
                            page.url.geturl()
                        )
                )

            else:
                # href's netloc wasn't an empty string, AND it was on a different domain than the target.
                # don't scan it.
                page.scanned = True
        return page

    def get_urls(self):
        return [(i.url.geturl(), i.status_code) for i in self.children]

    def get_parent_urls(self):
        return [i.url for i in self.parents]

    def add_child(self, href) -> None:
        match href:
            case str():
                p = self.get_page(href)
                self.children.add(p)
            case Page():
                self.children.add(href)
            case urllib.parse.ParseResult():
                p = self.get_page(href)
                self.children.add(p)
            case _:
                raise TypeError(f'Expected str or Page, got {type(href)}')

    def add_parent(self, href) -> None:
        match href:
            case str():
                p = self.get_page(href)
                self.parents.add(p)
            case Page():
                self.parents.add(href)
            case urllib.parse.ParseResult():
                p = self.get_page(href)
                self.parents.add(p)
            case _:
                raise TypeError(f'Expected str or Page, got {type(href)}')

    def scan(self) -> None:
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
                for a in soup.find_all('a'):
                    href = a.get('href')
                    if href:
                        p = self.get_page(href)
                        p.add_parent(self.url)
                        self.add_child(p)
                        self.website.add_child(p)

        except Exception as e:
            logging.error(f'Error while scanning {self.url.geturl()}, skipping.')
            logging.error(f'The error produced was {e}')


class App:
    def __init__(self, blacklist, target):
        self.blacklist = blacklist
        self.target = target
        self.session = requests.Session()

    def run(self):
        website = Page(self.target, self.target, self.session, self.blacklist)
        website.website = website
        website.scan()
 
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
    if len(sys.argv) == 1:
        print(f'Usage: python3 {__file__.rsplit("/")[-1]} mp4 png http://127.0.0.1')
        exit()

    logging.basicConfig(level = logging.INFO, format = '%(asctime)s:%(levelname)s:%(message)s')

    blacklist = sys.argv[1:-1]
    target = sys.argv[-1]
    app = App(blacklist, target)
    app.run()

