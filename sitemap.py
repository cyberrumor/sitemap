#!/usr/bin/env python3
from time import sleep
import sys
import os
import requests
from bs4 import BeautifulSoup
import urllib.parse

def sanitize(href, url, blacklist):
    if href.endswith('../'):
        return
    if any([href.count(i) for i in blacklist]):
        return
    if href.count('<') or href.count('>'):
        return
    if href.count('javascript:void(0)'):
        return

    u = urllib.parse.urljoin(url, href)
    r = u.split('?')[0]
    l = r.split('#')[0]

    clean = l.split('none')[0]
    if clean.endswith('/'):
        return clean.rstrip('/')
    return clean


def get_links(master, dom, url, soup, blacklist):
    emails = []
    hrefs = []
    subs = []
    misc = []

    for link in soup.find_all('a'):
        href = str(link.get('href')).lower().rstrip('/')

        # collect domain/s
        if not href.startswith('http') or href.startswith(master):

            if href.startswith('mailto:'):
                emails.append(href.lstrip('mailto:').lower())
                continue

            if href.count('@'):
                emails.append(href.lower())
                continue

            result = sanitize(href, url, blacklist)
            if result and result not in hrefs:
                hrefs.append(result)

        # collect sub.domains
        elif href.split('.', 1)[-1].startswith(dom):
            result = href[0:href.find(dom) + len(dom)]
            if result not in subs:
                subs.append(result)

        # eww, gross!
        else:
            if href not in misc:
                misc.append(href)

    return hrefs, emails, subs, misc

def get_forms(url, soup, blacklist):
    forms = []
    for form in soup.find_all('form'):
        href = form.attrs.get('action')
        if not href:
            continue

        href = href.lower()
        if not href.startswith('http') or href.startswith(url):

            result = sanitize(href, url, blacklist)
            if result:
                forms.append(result)

    return forms

def get_src(url, soup, blacklist):
    sources = []
    for tag in soup.find_all(src = True):
        tag_soup = BeautifulSoup(str(tag), 'html.parser')
        for dec in tag_soup.descendants:
            try:
                href = dec.attrs.get('src')
                if href:
                    result = sanitize(href, url, blacklist)
                    if result and result not in sources:
                        sources.append(result)
            except Exception as e:
                # until we can sort better, silently ignore dec with no attrs.
                # print(f'error: {e}. dec was {dec}, type(dec) was {type(dec)}')
                continue

    return sources

def get_click(url, soup, blacklist):
    sources = []
    for tag in soup.find_all(onclick = True):
        tag_soup = BeautifulSoup(str(tag), 'html.parser')
        for dec in tag_soup.descendants:
            href = dec.attrs.get('onclick')
            if href:
                result = sanitize(href, url, blacklist)
                if result and result not in sources:
                    sources.append(result)
    return sources

def get_robots(s, url, blacklist):
    hrefs = []
    try:
        r = s.get(url + '/robots.txt')
    except Exception as e:
        print(f'while trying to get /robots.txt: {e}')
        return hrefs

    for line in r.text.lower().split('\n'):
        if line.startswith('#'):
            # skip comments.
            continue

        if any([
        line.startswith('user-agent'),
        line.startswith('crawl-delay'),
        line.startswith('daumwebmastertool'), ]): 
            # these lines have useless key:values for us. skip.
            continue

        for word in line.split(' '):
            if not word.startswith('http') or word.startswith(url):

                if word in ['disallow:', 'allow:', 'sitemap:']:
                    # these are keys, we only care about the values. skip.
                    continue

                result = sanitize(word, url, blacklist)
                if result:
                    hrefs.append(result)

    return hrefs

def run(master, blacklist):
    dom = master.split('https://')[-1]
    dom = dom.split('http://')[-1]
    dom = dom.split('www.')[-1]
    dom = dom.split('/')[0]

    s = requests.Session()
    r = s.get(master)
    r.raise_for_status()

    webmap = []
    robolinks = get_robots(s, master, blacklist)
    for href in robolinks:
        if href.rstrip('/') not in webmap:
            webmap.append(href)

    emails = []
    forms = []
    subs = []
    misc = []
    sources = []
    # clicks = []

    i = 0
    rate_limit = 0

    # this is not a for loop because we have to append to webmap within the loop.
    while i < len(webmap):

        print(webmap[i], file = sys.stderr, flush = True)

        # we pick up some jankiness from /robots.txt
        if webmap[i].count('*'):
            # this will happen instantly. Only point of print is to preserve progress indicator
            # only necessary if last item in webmap gets skipped.
            print(f'skipping [{i + 1}/{len(webmap)}]: {webmap[i]}', flush = True, end = '\r')
            i += 1
            continue
        else:
            print(f'scanning [{i + 1}/{len(webmap)}]: {webmap[i]}', flush = True, end = '\r')


        # raise rate limit if we error out on request.
        try:
            r = s.get(webmap[i], timeout = rate_limit + 1)
        except Exception as e:
            rate_limit += 1
            print(f'error: {e}')
            print(f'raising rate limit to {rate_limit}')
            i += 1
            continue

        # make soup
        soup = BeautifulSoup(r.text, 'html.parser')

        # get forms and write them to forms.txt
        all_forms = get_forms(r.url, soup, blacklist)
        for form in all_forms:
            if form not in forms:
                forms.append(form)
                print(form, file = sys.stderr, flush = True)

        # get all src attribute values
        all_src = get_src(r.url, soup, blacklist)
        for source in all_src:
            if source not in sources:
                sources.append(source)
                print(source, file = sys.stderr, flush = True)


        # get all onclick attribute values
        #all_clicks = get_click(r.url, soup, blacklist)
        #for click in all_clicks:
        #    if click not in clicks:
        #        clicks.append(click)

        # get hrefs, emails, sub domains.
        all_hrefs, all_emails, all_subs, all_x = get_links(
                master,
                dom,
                r.url,
                soup,
                blacklist
            )

        # sort emails
        for email in all_emails:
            if email not in emails:
                emails.append(email)
                print(email, file = sys.stderr, flush = True)

        # sort sub domains
        for sub in all_subs:
            if sub not in subs:
                subs.append(sub)
                print(sub, file = sys.stderr, flush = True)

        # sort misc
        for m in all_x:
            if m not in misc:
                misc.append(m)
                print(m, file = sys.stderr, flush = True)

        # sort urls
        for ref in all_hrefs:
            if ref not in webmap:
                webmap.append(ref)
                print(ref, file = sys.stderr, flush = True)

        sleep(rate_limit)
        i += 1



if __name__ == '__main__':
    if not sys.argv[1:]:
        print('Usage: python3 main.py https://localhost.com 2>output.txt')
        print('Usage with blacklist cli: python3 main.py docs pdf jpg png mp4 mp3 https://localhost.com 2>output.txt')
        print('Usage with blacklist file: python3 main.py $(cat blacklist.txt) https://localhost.com 2>output.txt')
        exit()

    master = sys.argv[-1]
    blacklist = sys.argv[1:-1]

    run(master, blacklist)

    print('', flush = True)
    print('scan complete')




