# sitemap
Compiles a list of a website's subdomains, form action pages, emails, src references, and hrefs. Each href on the same subdomain is added to a list of pages to search for more resources. This effectively maps all publicly accessible locations on an entire website, and sometimes locations that were not intended to be publicly accessible. This is similar to Burp Suite's site mapping feature, but automates accessing pages so you don't have to click through their entire website to get a complete map. Useful for asset discovery, penetration testing, recon, and finding places that /sitemap.html excluded.

# Features
- Automatic rate limiting (without retry).
- Automatic robots.txt detection.
- Blacklist support. Pages with blacklisted keywords won't be accessed, but they will still appear in output.
- Progress indicator.
- Supports output redirection.

# Usage

Scan a whole site without accessing subdomains: ```python3 sitemap.py https://localhost.com```

Scan a specific subdomain without accessing other subdomains: ```python3 sitemap.py https://knownsubdomain.localhost.com```

Usage with blacklist cli: ```python3 sitemap.py jpg png pdf mp https://localhost.com```

Usage with blacklist file: ```python3 sitemap.py $(cat blacklist.txt) https://localhost.com```

Outputs the progress of the scan to stdout, outputs results to stderr. To output to a file, just use output redirection:
```python3 sitemap.py https://localhost.com 2>output.txt```

Deduplicate and sort output file:
```python3 deduplicate.py output.txt```
