import requests
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime
import argparse

def sanitize_filename(filename):
    """Removes invalid characters from a string so it can be used as a filename."""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def get_talk_links_fallback(conference_url, session_headers, year, month):
    """
    Fallback method to extract talk links when the primary method fails.
    Uses alternative approaches for conferences with different HTML structures.
    """
    try:
        response = requests.get(conference_url, headers=session_headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching conference page {conference_url}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    talk_links = set()
    base_domain = "https://www.churchofjesuschrist.org"

    # Method 1: Look for direct talk links in conference path
    pattern = f"/study/general-conference/{year}/{month}/"
    all_links = soup.find_all('a', href=True)
    
    for link in all_links:
        href = link.get('href', '')
        # Check for direct talk links - these have the conference pattern but aren't session pages
        if (pattern in href and 
            not href.endswith(f"/{month}") and  # not the main conference page
            not href.endswith(f"/{month}/") and
            not href.endswith(f"/{month}?lang=eng") and  # not the main conference page with lang
            '?lang=eng' in href and  # talks typically have lang parameter
            '-session' not in href and  # exclude session pages
            href != conference_url):  # not the same as the conference URL
            full_url = f"{base_domain}{href}" if href.startswith('/') else href
            talk_links.add(full_url)
    
    if talk_links:
        print(f"  Fallback method found {len(talk_links)} talk links using direct link pattern")
        return list(talk_links)
    
    # Method 2: Look for links with specific patterns that indicate talks
    # Some conferences use numbered or speaker-name based URLs
    for link in all_links:
        href = link.get('href', '')
        link_text = link.get_text(strip=True)
        
        # Check for patterns like /2024/10/12andersen or /2017/04/trust-in-the-lord-and-lean-not
        if (f"/general-conference/{year}/{month}/" in href and
            len(href.split('/')) >= 6 and  # has enough path components
            not any(exclude in href for exclude in ['-session', f'/{month}?', f'/{month}/', 'contents']) and
            ('?lang=eng' in href or not '?' in href)):  # either has lang param or no params
            
            # Additional check: make sure it's not a session page and has some content
            if link_text and len(link_text) > 10:  # talks usually have descriptive text
                full_url = f"{base_domain}{href}" if href.startswith('/') else href
                talk_links.add(full_url)
    
    if talk_links:
        print(f"  Fallback method found {len(talk_links)} talk links using extended pattern matching")
    
    return list(talk_links)

def get_talk_links(conference_url, session_headers):
    """
    Fetches the main conference page and extracts links to individual talks
    by finding list items with the attribute data-content-type="general-conference-talk".
    If that fails, uses fallback methods for conferences with different structures.
    """
    try:
        response = requests.get(conference_url, headers=session_headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching conference page {conference_url}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    talk_links = set()
    base_domain = "https://www.churchofjesuschrist.org"

    # Primary method: Find all list items specifically marked as a "general-conference-talk"
    talk_list_items = soup.select('li[data-content-type="general-conference-talk"]')

    for item in talk_list_items:
        # Find the anchor tag within the list item
        link_tag = item.find('a', href=True)
        if link_tag:
            href = link_tag['href']
            # Prepend the domain to make the relative URL absolute.
            full_url = f"{base_domain}{href}"
            talk_links.add(full_url)

    if talk_links:
        return list(talk_links)
    
    # If primary method failed, try fallback methods
    print(f"  Primary method found no talks, trying fallback methods...")
    
    # Extract year and month from URL for fallback
    url_parts = conference_url.split('/')
    year = url_parts[-2] if len(url_parts) >= 2 else None
    month = url_parts[-1].split('?')[0] if len(url_parts) >= 1 else None
    
    if year and month:
        return get_talk_links_fallback(conference_url, session_headers, year, month)
    
    return []

def get_talk_text(talk_url, session_headers):
    """
    Fetches an individual talk page and extracts the title, speaker, and body text,
    preserving paragraph breaks.
    """
    try:
        response = requests.get(talk_url, headers=session_headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching talk page {talk_url}: {e}")
        return None, None, None

    soup = BeautifulSoup(response.content, 'html.parser')

    title_element = soup.find('h1')
    title = title_element.get_text(strip=True) if title_element else "No Title Found"

    speaker_element = soup.find('p', class_='author-name')
    speaker = speaker_element.get_text(strip=True) if speaker_element else "No Speaker Found"
    speaker = speaker.replace('By ', '')  # Remove "By " prefix if it exists

    body_element = soup.find('div', class_='body-block')
    if not body_element:
        return title, speaker, "Could not find talk body."

    # Find all the paragraph tags
    paragraphs = body_element.select('p:not(.study-note)')
    
    processed_paragraphs = []
    for p in paragraphs:
        # Get the text from a single paragraph, using separator=' ' to fix word squishing
        # and strip=True to remove leading/trailing whitespace.
        para_text = p.get_text(separator=' ', strip=True)
        processed_paragraphs.append(para_text)

    # Join the list of cleaned paragraphs together with double newlines.
    talk_text = '\n\n'.join(processed_paragraphs)

    return title, speaker, talk_text


def main():
    """
    Main function to orchestrate the downloading and saving of talks.
    """
    parser = argparse.ArgumentParser(description='Download General Conference talks of the Church of Jesus Christ of Latter-day Saints')
    parser.add_argument('--start-year', type=int, default=2000, 
                       help='Starting year for downloading talks (default: 2000)')
    parser.add_argument('--end-year', type=int, default=datetime.now().year,
                       help='Ending year for downloading talks (default: current year)')
    parser.add_argument('--output-dir', type=str, default='./data/General_Conference_Talks/',
                       help='Output directory for saved talks (default: ./data/General_Conference_Talks/)')
    
    args = parser.parse_args()

    # Initialize failure tracking
    failed_conferences = []
    failed_talks = []
    total_conferences = 0
    total_talks_processed = 0
    total_talks_saved = 0

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    base_url = "https://www.churchofjesuschrist.org/study/general-conference"
    start_year = args.start_year
    current_year = datetime.now().year
    if (args.end_year < start_year):
        print(f"Error: end_year ({args.end_year}) cannot be less than start_year ({start_year}).")
        return
    # Ensure end_year does not exceed the current year
    if args.end_year > current_year:
        print(f"Warning: end_year ({args.end_year}) is greater than the current year ({current_year}). Setting end_year to {current_year}.")
    end_year = min(args.end_year, current_year)  # Don't go beyond current year
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    for year in range(start_year, end_year + 1):
        # Conferences are in April (04) and October (10)
        for month in ['04', '10']:
            conference_url = f"{base_url}/{year}/{month}?lang=eng"
            month_str = 'April' if month == '04' else 'October'
            
            # Skip future conferences
            if year == current_year and int(month) > datetime.now().month and month_str == 'October':
                 continue
            if year == current_year and int(month) > datetime.now().month and month_str == 'April':
                 continue

            total_conferences += 1
            conference_name = f"{year} {month_str}"
            print(f"--- Processing {conference_name} Conference ---")
            print(f"Fetching from: {conference_url}")

            talk_links = get_talk_links(conference_url, headers)

            if not talk_links:
                print(f"No talks found for this conference.")
                failed_conferences.append({
                    'conference': conference_name,
                    'url': conference_url,
                    'reason': 'No talks found'
                })
                print("-" * 20)
                continue

            year_dir = os.path.join(output_dir, str(year))
            month_dir = os.path.join(year_dir, month)
            os.makedirs(month_dir, exist_ok=True)

            print(f"Found {len(talk_links)} talks.")
            conference_talk_count = 0
            for link in sorted(talk_links): # Sorting makes the output more predictable
                total_talks_processed += 1
                title, speaker, text = get_talk_text(link, headers)
                if title and speaker and text:
                    safe_speaker = sanitize_filename(speaker)
                    safe_title = sanitize_filename(title)
                    filename = os.path.join(month_dir, f"{safe_speaker}_{safe_title}.txt")
                    try:
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(f"Title: {title}\n")
                            f.write(f"Speaker: {speaker}\n")
                            f.write(f"URL: {link}\n\n")
                            f.write(text)
                        print(f"  Successfully saved: {safe_speaker}_{safe_title}.txt")
                        total_talks_saved += 1
                        conference_talk_count += 1
                    except IOError as e:
                        print(f"  Error saving file {filename}: {e}")
                        failed_talks.append({
                            'conference': conference_name,
                            'url': link,
                            'title': title,
                            'speaker': speaker,
                            'reason': f'File save error: {e}'
                        })
                else:
                    print(f"  Could not process talk: {link}")
                    failed_talks.append({
                        'conference': conference_name,
                        'url': link,
                        'title': title or 'Unknown',
                        'speaker': speaker or 'Unknown',
                        'reason': 'Could not extract talk content'
                    })
            
            # Check if no talks were successfully saved for this conference
            if conference_talk_count == 0 and talk_links:
                failed_conferences.append({
                    'conference': conference_name,
                    'url': conference_url,
                    'reason': f'Found {len(talk_links)} talk links but could not save any talks'
                })
            
            print("-" * 20)

    # Report summary and failures
    print(f"\n📊 --- DOWNLOAD SUMMARY ---")
    print(f"Total conferences processed: {total_conferences}")
    print(f"Total talks processed: {total_talks_processed}")
    print(f"Total talks successfully saved: {total_talks_saved}")
    print(f"Failed conferences: {len(failed_conferences)}")
    print(f"Failed individual talks: {len(failed_talks)}")

    if failed_conferences:
        print(f"\n❌ --- FAILED CONFERENCES ---")
        for failure in failed_conferences:
            print(f"  • {failure['conference']}: {failure['reason']}")
            print(f"    URL: {failure['url']}")

    if failed_talks:
        print(f"\n❌ --- FAILED TALKS ---")
        for failure in failed_talks:
            print(f"  • {failure['conference']} - {failure['speaker']}: {failure['title']}")
            print(f"    Reason: {failure['reason']}")
            print(f"    URL: {failure['url']}")

    if not failed_conferences and not failed_talks:
        print(f"\n✅ --- All downloads completed successfully! ---")
    else:
        print(f"\n⚠️  --- Download completed with {len(failed_conferences)} failed conferences and {len(failed_talks)} failed talks ---")

if __name__ == "__main__":
    main()