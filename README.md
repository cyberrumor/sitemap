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

Outputs to folder called `output`, references are sorted by type, alphabetically, in the following files:
- `href.txt` = hrefs on the same domain, stripped of arguments. Additions here are crawled.
- `mailto.txt` = any "mailto:" addresses, or any other href containing "@", not crawled.
- `href_subdomains.txt` = hrefs on subdomains of original target, stripped of arguments, not crawled.
- `href_external.txt` = hrefs leading offsite, with arguments, not crawled.
- `src.txt` = "src" value of any tag containing "src" key, not crawled.
- `action.txt` = form action pages, not crawled.
- `onclick.txt` = "onclick" value of any tag containing "onclick" key, not crawled.


