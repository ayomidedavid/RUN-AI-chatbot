import os
import requests
from bs4 import BeautifulSoup

# Define scraping target
RUN_URLS = [
    "https://run.edu.ng/news/",
    "https://run.edu.ng/about-us/"
]

def crawl_run_portal(url):
    print(f"Crawling: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return ""
        
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract headers and paragraphs
    extracted_lines = []
    
    # Common main content blocks
    main_content = soup.find('main') or soup.find('div', class_='content') or soup.body
    
    if main_content:
        for element in main_content.find_all(['h1', 'h2', 'h3', 'p']):
            text = element.get_text(separator=' ', strip=True)
            if text and len(text) > 20: # Filter out menus or small ui tokens
                extracted_lines.append(text)
                
    return "\n\n".join(extracted_lines)

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Path to the extracted data file
    data_file = os.path.join(script_dir, "extracted_data.txt")
    # Collect raw scraped content from each URL
    scraped_content = []
    for url in RUN_URLS:
        content = crawl_run_portal(url)
        if content:
            scraped_content.append(content)
    # Load any existing content from the file, if it exists
    existing_content = []
    if os.path.isfile(data_file):
        with open(data_file, "r", encoding="utf-8") as f:
            file_text = f.read().strip()
            if file_text:
                # Split on double newlines to keep original paragraph grouping
                existing_content = [p.strip() for p in file_text.split("\n\n") if p.strip()]
    # Combine existing and new scraped content
    combined_content = existing_content + scraped_content
    # Clean and deduplicate extracted lines across all content
    cleaned_lines = []
    seen = set()
    for block in combined_content:
        for line in block.split("\n"):
            stripped = line.strip()
            if stripped and stripped not in seen:
                seen.add(stripped)
                cleaned_lines.append(stripped)
    final_text = "\n\n".join(cleaned_lines)
    print(f"Crawling complete. Extracted {len(final_text)} characters.")
    if len(final_text) > 100:
        # Overwrite the file to replace old data with new extraction
        with open(data_file, "w", encoding="utf-8") as f:
            f.write(final_text)
        print(f"Successfully wrote scraped knowledge to {data_file}.")
    else:
        print("No meaningful content extracted.")
