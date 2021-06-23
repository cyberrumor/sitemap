#!/usr/bin/env python3
from time import sleep
import sys
import requests
from bs4 import BeautifulSoup
import urllib.parse

def get_links(url, soup, blacklist):
    emails = []
    hrefs = []
    for link in soup.find_all('a'):
        href = str(link.get('href'))
        if not href.startswith('http') or href.startswith(url):

            if href.endswith('../') or href.endswith('.pdf'):
                continue

            if any([href.count(i) for i in blacklist]):
                continue

            if href.startswith('mailto:'):
                emails.append(href.lstrip('mailto:').lower())
                continue

            if href.count('@'):
                emails.append(href.lower())
                continue

            u = urllib.parse.urljoin(url, href)
            r = u.split('?')[0]
            l = r.split('#')[0]

            if l.count('None'):
                clean = l.rstrip('None')
            else:
                clean = l

            if clean.endswith('/'):
                url = clean.rstrip('/')
            else:
                url = clean

            hrefs.append(url)

    return hrefs, emails

def get_robots(url, blacklist):
    hrefs = []
    try:
        r = s.get(url + '/robots.txt')
    except Exception as e:
        print(f'while trying to get /robots.txt: {e}')
        return hrefs

    for line in r.text.lower().split('\n'):

        for word in line.split(' '):
            if not word.startswith('http') or word.startswith(url):
                if word.endswith('../') or word.endswith('.pdf'):
                    continue
                if any([word.count(i) for i in blacklist]):
                    continue
                if word in ['user-agent:', 'disallow:', 'sitemap:']:
                    continue
                if not word.count('/'):
                    continue

                u = urllib.parse.urljoin(url, word)
                r = u.split('?')[0]
                l = r.split('#')[0]
                clean = l.rstrip('None')
                url = clean.rstrip('/')
                hrefs.append(url)

    return hrefs


if __name__ == '__main__':
    if sys.argv[1:]:
        url = sys.argv[-1]
        blacklist = sys.argv[1:-1]
    else:
        print('Usage: python3 main.py docs comment https://localhost.com')
        print('Usage: python3 main.py $(cat blacklist.txt) https://localhost.com')
        exit()

    s = requests.Session()
    r = s.get(url)
    r.raise_for_status()

    webmap = [{'url': r.url}]
    robolinks = get_robots(url, blacklist)
    for href in robolinks:
        if href.rstrip('/') not in [i['url'] for i in webmap]:
            webmap.append({'url': href})

    emails = []
    i = 0
    rate_limit = 0
    with open('output.txt', 'w') as output:
        while i < len([target['url'] for target in webmap]):
            # we pick up some jankiness from /robots.txt
            if webmap[i]['url'].count('*'):
                output.write(f"{webmap[i]['url']}\n")
                print(f'skipping: {webmap[i]["url"]}')
                continue

            print(f'scanning: {webmap[i]["url"]}')
            # raise rate limit if we error out on request.
            try:
                r = s.get(webmap[i]['url'])
            except Exception as e:
                rate_limit += 1
                print(f'error: {e}')
                print(f'raising rate limit to {rate_limit}')
                i += 1
                continue

            # make soup
            soup = BeautifulSoup(r.text, 'lxml')

            # expand list of targets via parsing for hrefs sharing target's domain
            all_hrefs, all_emails = get_links(r.url, soup, blacklist)
            hrefs = []
            for email in all_emails:
                if email not in emails:
                    emails.append(email)
                    with open('emails.txt', 'a') as email_output:
                        email_output.write(f'{email}\n')

            for ref in all_hrefs:
                if ref not in hrefs:
                    hrefs.append(ref)

            webmap_links = [target['url'] for target in webmap]
            for ref in hrefs:
                if ref not in webmap_links:
                    webmap.append({'url': str(ref)})
                    output.write(f'{ref}\n')


            sleep(rate_limit)
            i += 1






