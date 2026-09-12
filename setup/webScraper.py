"""
Web Scraper specifically designed for a specific wordpress website. (may work for others!)
Gathers info from main page to traverse blog pages & scrape blog page data such as Titles, Subheaders, and Body content.

Usage:
    python3 setup/webScraper.py --start-page 1 --end-page 30
	python3 setup/webScraper.py 		# Starts at page 1 to max page number
"""
from pathlib import Path
from bs4 import BeautifulSoup as bs
from dotenv import load_dotenv

import argparse, contextlib, html, logging, re, time, requests, os

# Setup logging
log = logging.getLogger("pyWebScraper")

# Setup globals
load_dotenv(Path(__file__).parent.parent / ".env")
_BASE_URL = os.getenv('DEFAULT_BASE_URL')
_OUTPUT_NAMES = {"title": "titleTexts.txt", "subhead": "subheadTexts.txt", "article": "articleTexts.txt"}

# Target site is a wordpress site - setting custom user agent to bypass any restrictions
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:155.0) Gecko/20100101 Firefox/155.0"}

# Get URL response
# Params: url (string) - url to query
# Return: response (requests.Response object) - website response
def _get_response(url):
    response = requests.get(url, timeout=30, headers=_HEADERS)
    response.raise_for_status()
    return response

# Get max page number
# Params: base_url (string) - base url we will build off to get max page number
# Return: max_page_number (integer) - max number of pages we can query (default 1)
def get_max_page(base_url):
    response = _get_response(f"{base_url}/articles/page/1/")
    soup = bs(response.content, "html.parser")
    numbers = []
    for chunk in soup.find_all("a", class_="page-numbers"):
        found = re.findall(r"\d+", chunk.get("href", ""))
        if found:
            numbers.append(int(found[-1]))
    return max(numbers) if numbers else 1


# Iterate through all blog listing pages - calls follow
# Params:
#   start (integer) - page to start on (default 1)
#   end (integer) - page to end on (default max_page_number)
#   delay (float) - time delay between scrapes (avoid rate-limit)
#   base_url (string) - base url of the site we are scraping
# Return: None
def iterate_pages(start, end, delay, base_url):
    print(base_url)
    for i in range(start, end + 1):
        url = f"{base_url}/articles/page/{i}/"
        log.info("Parsing page %s", url)
        time.sleep(delay)
        try:
            response = _get_response(url)
        except requests.RequestException as e:
            log.warning("Fetching %s failed: %s". url, e)
            continue
        soup = bs(response.content, "html.parser")
        for article in soup.find_all("article", class_="article-card"):
            link = article.find("a", rel="nofollow")
            if link and link.get("href"):
                yield link["href"]


# Drills down into blog post
# Params:
#   url (string) - url of specified blog post to scrape
#   writers (dictionary) - dictionary of file handlers
#                          K:V = element:filepath
#   delay (float) - time delay between scrapes (avoid rate-limits)
# Return: None
def follow_blog(url, writers, delay):
    log.info("Scraping %s", url)
    time.sleep(delay)
    try:
        response = _get_response(url)
    except requests.RequestException as e:
        log.warning("follow_blog failed for %s: %s", url, e)
        return

    soup = bs(response.content, "html.parser")
    title = soup.find("title")
    paragraphs = soup.find_all("p", class_="wp-block-paragraph")
    subheaders = soup.find_all("h2", class_="wp-block-heading")
    if title is None or not paragraphs:
        log.warning("Blog post skipped %s: no title or body", url)
        return
    writers["title"].write(html.unescape(title.get_text()).strip() + "\n")
    for paragraph in paragraphs:
        writers["article"].write(html.unescape(paragraph.get_text()).strip() + "\n\n")
    for subheader in subheaders:
        writers["subhead"].write(html.unescape(subheader.get_text()).strip() + "\n")

# Parse command-line arguments
# Params: argv (string[]) - command line arguments
# Return: None
def _parse_args(argv):
    ap = argparse.ArgumentParser(description="Wordpress webscraper for specific website to train model")
    ap.add_argument("--start-page", type=int, default=1)
    ap.add_argument("--end-page", type=int, default=None)
    ap.add_argument("--delay", type=float, default=2.0)
    ap.add_argument("--base-url", default=_BASE_URL)
    ap.add_argument("--out-dir", default="corpus")
    ap.add_argument("--append", action="store_true")
    return ap.parse_args(argv)

# Main routine
# Params: argv (default none; string[]) - command line arguments
# Return: None
def main(argv=None):
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = _parse_args(argv)
    
    if args.end_page is not None:
        end = args.end_page
    else:
        end = get_max_page(args.base_url)
    
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    if args.append:
        mode = "a"
    else:
        mode = "w"
    
    with contextlib.ExitStack() as stack:
        writers = {
                key: stack.enter_context(open(out_dir / name, mode, encoding="utf-8"))
                for key, name in _OUTPUT_NAMES.items()
                }
        for link in iterate_pages(args.start_page, end, args.delay, args.base_url):
            follow_blog(link, writers, args.delay)
    log.info("Wrote corpus to %s", out_dir)

if __name__ == "__main__":
	main()
