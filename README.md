# sitemap
Compiles a list of a website's subdomains and hrefs. Each href on the same subdomain is added to a list of pages to search for more resources. This effectively maps all publicly accessible locations on an entire website, and sometimes locations that were not intended to be publicly accessible. This is similar to Burp Suite's site mapping feature, but automates accessing pages so you don't have to click through their entire website to get a complete map. Useful for asset discovery, penetration testing, recon, and finding places that /sitemap.html excluded.

# Usage

Scan a whole site without accessing subdomains: ```python3 sitemap.py https://localhost.com```

Scan a specific subdomain without accessing other subdomains: ```python3 sitemap.py https://knownsubdomain.localhost.com```

Usage with blacklist: ```python3 sitemap.py jpg png pdf mp https://localhost.com```

Usage with blacklist file: ```python3 sitemap.py $(cat blacklist.txt) https://localhost.com```


# Planned Features

- automatic rate limiting
- robots.txt parsing
- form action page detection
- switch to ignore parameters (currently a url with parameters is treated as a unique location).


