import requests
from xml.etree import ElementTree as ET
from data_processing import process_url
from utils import append_to_excel, generate_jsonl_from_excel, load_processed_urls, cleanup_excel
import random

# URLs of the sitemaps
sitemap_urls = [
    "https://refugies.info/sitemap-index/sitemap-index-fr/sitemap-index-demarches.xml",
    "https://refugies.info/sitemap-index/sitemap-index-fr/sitemap-index-dispositifs.xml",
    "https://qx1.org/experience-sitemap.xml",
    "https://qx1.org/place-sitemap.xml",
    "https://qx1.org/story-sitemap.xml",
    "https://exil-solidaire.fr/api/sitemap.xml"
]

EXCEL_FILE_PATH = "output.xlsx"
JSONL_FILE_PATH = "output.jsonl"

def main():
    all_urls = []
    processed_urls = load_processed_urls()

    # Generate JSONL from Excel on startup
    cleanup_excel(EXCEL_FILE_PATH)
    generate_jsonl_from_excel(EXCEL_FILE_PATH, JSONL_FILE_PATH)

    for sitemap_url in sitemap_urls:
        urls = fetch_and_parse_urls(sitemap_url)
        print(f"Fetched {len(urls)} URLs from {sitemap_url}")
        all_urls.extend(urls)

    # Shuffle the URLs randomly
    random.shuffle(all_urls)

    print(f"Total URLs to process: {len(all_urls)}")

    for url in all_urls:
        if url in processed_urls:
            print(f"Skipping already processed URL: {url}")
            continue
        print(f"Processing: {url}")
        original_text, response = process_url(url)
        if original_text and response:
            append_to_excel(url, original_text, response, excel_file_path=EXCEL_FILE_PATH)
            # Regenerate JSONL after saving to Excel
            generate_jsonl_from_excel(EXCEL_FILE_PATH, JSONL_FILE_PATH)

# Function to fetch URLs from a sitemap
def fetch_and_parse_urls(sitemap_url):
    response = requests.get(sitemap_url, headers={'Accept': 'application/xml'})
    response.raise_for_status()

    root = ET.fromstring(response.content)
    urls = []

    for url_element in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
        loc_element = url_element.find('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
        if loc_element is not None:
            urls.append(loc_element.text)

    return urls

if __name__ == "__main__":
    main()
