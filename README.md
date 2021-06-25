# sitemap
Collects a domain's internal pages, subdomains, form action pages, emails, and external hrefs.


This is technically a spider, not a fuzzer. It's way faster than a fuzzer because it doesn't have to guess locations to find them.

Accepts blacklists from the command line (or via concatenating a blacklist file) and also collects emails.

It will try to stay on the same domain, but some anomolous behavior prevents me from

making a guarantee at this time. Any links collected will be subsiquently crawled for

additional links. Automatic rate limiting without retry.

Usage: ```python3 main.py https://localhost.com```

Usage with blacklist cli: ```python3 main.py jpg png pdf mp https://localhost.com```

Usage with blacklist file: ```python3 main.py $(cat blacklist.txt) https://localhost.com```



