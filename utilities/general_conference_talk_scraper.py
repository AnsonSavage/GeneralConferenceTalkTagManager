import requests
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime

def sanitize_filename(filename):
    """Removes invalid characters from a string so it can be used as a filename."""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def get_talk_links(conference_url, session_headers):
    """
    Fetches the main conference page and extracts links to individual talks
    by finding list items with the attribute data-content-type="general-conference-talk".
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

    # Find all list items specifically marked as a "general-conference-talk"
    # as per your excellent suggestion. This is a very reliable selector.
    talk_list_items = soup.select('li[data-content-type="general-conference-talk"]')

    for item in talk_list_items:
        # Find the anchor tag within the list item
        link_tag = item.find('a', href=True)
        if link_tag:
            href = link_tag['href']
            # Prepend the domain to make the relative URL absolute.
            full_url = f"{base_domain}{href}"
            talk_links.add(full_url)

    return list(talk_links)

def get_talk_text(talk_url, session_headers):
    """
    Fetches an individual talk page and extracts the title, speaker, and body text.
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

    # The speaker's name is in a <p> tag with the class 'author-name'
    speaker_element = soup.find('p', class_='author-name')
    speaker = speaker_element.get_text(strip=True) if speaker_element else "No Speaker Found"

    # The main text is in a <div> with the class 'body-block'
    body_element = soup.find('div', class_='body-block')
    if not body_element:
        return title, speaker, "Could not find talk body."

    # Select all paragraphs but exclude the small footnote markers
    paragraphs = body_element.select('p:not(.study-note)')
    talk_text = '\n\n'.join(p.get_text(strip=True) for p in paragraphs)

    return title, speaker, talk_text

def main():
    """
    Main function to orchestrate the downloading and saving of talks.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    base_url = "https://www.churchofjesuschrist.org/study/general-conference"
    start_year = 2000
    # The script will run up to and including the current year.
    current_year = datetime.now().year
    output_dir = "General_Conference_Talks"
    os.makedirs(output_dir, exist_ok=True)

    for year in range(start_year, current_year + 1):
        # Conferences are in April (04) and October (10)
        for month in ['04', '10']:
            conference_url = f"{base_url}/{year}/{month}?lang=eng"
            month_str = 'April' if month == '04' else 'October'
            
            # Skip future conferences
            if year == current_year and int(month) > datetime.now().month and month_str == 'October':
                 continue
            if year == current_year and int(month) > datetime.now().month and month_str == 'April':
                 continue

            print(f"--- Processing {year} {month_str} Conference ---")
            print(f"Fetching from: {conference_url}")

            talk_links = get_talk_links(conference_url, headers)

            if not talk_links:
                print(f"No talks found for this conference.")
                print("-" * 20)
                continue

            year_dir = os.path.join(output_dir, str(year))
            month_dir = os.path.join(year_dir, month)
            os.makedirs(month_dir, exist_ok=True)

            print(f"Found {len(talk_links)} talks.")
            for link in sorted(talk_links): # Sorting makes the output more predictable
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
                    except IOError as e:
                        print(f"  Error saving file {filename}: {e}")
                else:
                    print(f"  Could not process talk: {link}")
            print("-" * 20)

    print("\n✅ --- Download complete! ---")

if __name__ == "__main__":
    main()