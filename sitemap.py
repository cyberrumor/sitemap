#!/usr/bin/env python3
from time import sleep
import sys
import os
import requests
from bs4 import BeautifulSoup
import urllib

class Page:

    def __init__(self, website, url, blacklist = None):
        self.website = website
        self.url = urllib.parse.urlparse(url)
        self.children = set(())
        self.parents = set(())
        self.scanned = False
        self.blacklist = blacklist

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
                p = Page(self.website, href)
                # don't scan domains different from user input
                if p.url.hostname != self.website.url.hostname:
                    p.scanned = True
                return p

            case urllib.parse.ParseResult():
                for p in self.website.children:
                    if p.url.geturl() == href.geturl():
                        return p
                # the page is unique
                p = Page(self.website, href.geturl()) # make sure geturl return str
                # don't scan domains different from user input
                if p.url.hostname != self.website.url.hostname:
                    p.scanned = True
                return p


    def get_urls(self):
        return [i.url.geturl() for i in self.children]


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
        r = requests.get(self.url.geturl())
        if r.status_code:
            soup = BeautifulSoup(r.text, 'html.parser')
            for a in soup.find_all('a'):
                href = a.get('href')
                if href:
                    p = self.get_page(href)
                    p.add_parent(self.url)
                    self.add_child(p)
                    self.website.add_child(p)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print(f'Usage: python3 {__file__.rsplit("/")[-1]} mp4 png http://127.0.0.1')
        exit()

    blacklist = sys.argv[1:-1]
    target = sys.argv[-1]

    print(f'blacklist: {blacklist}')
    print(f'target: {target}')
    print()

    website = Page(target, target, blacklist = [])
    website.website = website
    website.scan()

    print(website.url.geturl())

    while not all([i.scanned for i in website.children]):
        for page in [i for i in website.children if not i.scanned]:
            if page.scanned:
                continue
            page.scan()

    for i in website.get_urls():
        print(i)

    print()
