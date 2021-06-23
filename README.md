# sitemap
Get all hrefs, including robots.txt and previously collected hrefs.

Accepts blacklists from the command line (or via concatenating a blacklist file) and also collects emails.


Usage: ```python3 main.py https://localhost.com```

Usage with blacklist cli: ```python3 main.py jpg png pdf mp https://localhost.com```

Usage with blacklist file: ```python3 main.py $(cat blacklist.txt) https://localhost.com```



