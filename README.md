# sitemap
Collects a website's internal hrefs, subdomains, form action pages, emails, src references, onclick references, and external hrefs.


This is technically a spider, not a fuzzer. It's way faster than a fuzzer because it doesn't have to guess locations to find them.

Accepts blacklists from the command line (or via concatenating a blacklist file).

It will try to stay on the same domain, but some anomolous behavior prevents me from

making a guarantee at this time. Any links collected will be subsiquently crawled for

additional links. Automatic rate limiting without retry.

Usage: ```python3 main.py https://localhost.com```

Usage with blacklist cli: ```python3 main.py jpg png pdf mp https://localhost.com```

Usage with blacklist file: ```python3 main.py $(cat blacklist.txt) https://localhost.com```

Outputs status to stdout, outputs goodies to stderr. To output to a file, just use output redirection:
```python3 main.py https://localhost.com 2>output.txt```

