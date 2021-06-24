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

            if href.endswith('../'):
                continue

            # check blacklist and also ensure accuracy of href collection
            if any([href.count(i) for i in blacklist]):
                continue

            # filter bad href collections
            if href.count('<') or href.count('>'):
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

def get_forms(url, soup, blacklist):
    forms = []
    for form in soup.find_all('form'):
        href = form.attrs.get('action')
        if not href:
            continue
        if not href.startswith('http') or href.startswith(url):
            if href.endswith('../'):
                continue
            if any([href.count(i) for i in blacklist]):
                continue
            if href.count('<') or href.count('>'):
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

            forms.append(url)

    return forms




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

                if word.endswith('../'):
                    continue

                if any([word.count(i) for i in blacklist]):
                    continue

                if word.count('<') or word.count('>'):
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
    with open('output.txt', 'w') as output, open('emails.txt', 'w') as email_output, open('forms.txt', 'w') as form_output:
        while i < len([target['url'] for target in webmap]):
            # we pick up some jankiness from /robots.txt
            if webmap[i]['url'].count('*'):
                output.write(f"{webmap[i]['url']}\n")
                print(f'skipping: {webmap[i]["url"]}')
                i += 1
                continue

            print(f'scanning: {webmap[i]["url"]}')
            # raise rate limit if we error out on request.
            try:
                r = s.get(webmap[i]['url'], timeout = 2)
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
                    form_output.write(f'{form}\n')

            # get hrefs and emails, add emails to emails.txt
            all_hrefs, all_emails = get_links(r.url, soup, blacklist)
            for email in all_emails:
                if email not in emails:
                    emails.append(email)
                    email_output.write(f'{email}\n')

            # de-duplicate hrefs
            hrefs = []
            for ref in all_hrefs:
                if ref not in hrefs:
                    hrefs.append(ref)

            # add unique links to webmap, write them to output.txt
            webmap_links = [target['url'] for target in webmap]
            for ref in hrefs:
                if ref not in webmap_links:
                    webmap.append({'url': str(ref)})
                    output.write(f'{ref}\n')

            sleep(rate_limit)
            i += 1






