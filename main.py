#!/usr/bin/env python3
from time import sleep
import sys
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

    if l.count('none'):
        clean = l.rstrip('none')
    else:
        clean = l

    if clean.endswith('/'):
        return clean.rstrip('/')
    else:
        return clean

def get_links(url, soup, blacklist):
    emails = []
    hrefs = []
    for link in soup.find_all('a'):
        href = str(link.get('href'))
        if not href.startswith('http') or href.startswith(url):

            if href.startswith('mailto:'):
                emails.append(href.lstrip('mailto:').lower())
                continue

            if href.count('@'):
                emails.append(href.lower())
                continue

            result = sanitize(href.lower(), url, blacklist)
            if result and result not in hrefs:
                hrefs.append(result)

    return hrefs, emails

def get_forms(url, soup, blacklist):
    forms = []
    for form in soup.find_all('form'):
        href = form.attrs.get('action')
        if not href:
            continue

        if not href.startswith('http') or href.startswith(url):

            result = sanitize(href.lower(), url, blacklist)
            if result:
                forms.append(result)

    return forms

def get_robots(url, blacklist):
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

                result = sanitize(word.lower(), url, blacklist)
                if result:
                    hrefs.append(result)

    return hrefs


if __name__ == '__main__':
    if sys.argv[1:]:
        url = sys.argv[-1]
        blacklist = sys.argv[1:-1]

    else:
        print('Usage: python3 main.py https://localhost.com')
        print('Usage with blacklist cli: python3 main.py docs pdf jpg png mp4 mp3 https://localhost.com')
        print('Usage with blacklist file: python3 main.py $(cat blacklist.txt) https://localhost.com')
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
    forms = []
    i = 0
    rate_limit = 0

    with (
    open('out.txt', 'w') as out,
    open('emails.txt', 'w') as e_out,
    open('forms.txt', 'w') as f_out):

        while i < len([target['url'] for target in webmap]):
            # we pick up some jankiness from /robots.txt
            if webmap[i]['url'].count('*'):
                out.write(f"{webmap[i]['url']}\n")
                print(f'skipping: {webmap[i]["url"]}')
                i += 1
                continue

            print(f'scanning: {webmap[i]["url"]}')
            # raise rate limit if we error out on request.
            try:
                r = s.get(webmap[i]['url'], timeout = rate_limit + 1)
            except Exception as e:
                rate_limit += 1
                print(f'error: {e}')
                print(f'raising rate limit to {rate_limit}')
                i += 1
                continue

            # make soup
            soup = BeautifulSoup(r.text, 'lxml')

            # get forms and write them to forms.txt
            all_forms = get_forms(r.url, soup, blacklist)
            for form in all_forms:
                if form not in forms:
                    forms.append(form)
                    f_out.write(f'{form}\n')

            # get hrefs and emails, add emails to emails.txt
            all_hrefs, all_emails = get_links(r.url, soup, blacklist)
            for email in all_emails:
                if email not in emails:
                    emails.append(email)
                    e_out.write(f'{email}\n')

            # add unique links to webmap, write them to out.txt
            webmap_links = [target['url'] for target in webmap]
            for ref in all_hrefs:
                if ref not in webmap_links:
                    webmap.append({'url': str(ref)})
                    out.write(f'{ref}\n')

            sleep(rate_limit)
            i += 1






