import requests
from bs4 import BeautifulSoup
import re
import os
import sys
import time

# Define headers to mimic a browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
}

def get_soup(url):
    """Helper function to get parsed HTML"""
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return BeautifulSoup(response.content, 'lxml')
    else:
        print(f"Failed to fetch {url}, status code: {response.status_code}")
        return None

def is_search_page(url):
    """Check if the provided URL is a search page (contains '?search=')"""
    return '?search=' in url

def extract_search_query(url):
    """Extract and format the search query from the URL"""
    query = re.search(r'\?search=([^&]+)', url)
    if query:
        search_text = query.group(1).replace('%20', ' ')  # Replace encoded spaces with actual spaces
        # Capitalize each word in the search text
        return ' '.join(word.capitalize() for word in search_text.split())
    return "Unknown_Search"

def extract_album_title(soup):
    """Extract album title from <h1> tag if available"""
    title_tag = soup.find('h1', class_="text-[24px] font-bold text-dark dark:text-white")
    if title_tag:
        return title_tag.text.strip()
    return "Unnamed_Album"

def find_album_links_from_search(base_url):
    """Function to find all album links from the search results page"""
    page = 1
    album_links = []

    while True:
        # Modify the base_url to add page parameter if necessary
        search_url = f"{base_url}&page={page}" if page > 1 else base_url
        soup = get_soup(search_url)

        if not soup:
            print(f"Failed to fetch page {page}")
            break
        
        # Find album links on the current search page
        found = False
        for link in soup.find_all('a', href=True):
            if re.search(r"https://bunkrrr\.org/a/\w+", link['href']):
                album_links.append(link['href'])
                found = True
        
        # If no more albums found on this page, stop
        if not found:
            break
        
        page += 1
    
    return album_links

def find_media_links(album_url):
    """Function to find all image and video tile links on the album page"""
    soup = get_soup(album_url)
    if not soup:
        return []
    
    # Find all links similar to image and video link patterns
    media_links = []
    for link in soup.find_all('a', href=True):
        if re.search(r"https://bunkrrr.org/i/\w+", link['href']):  # Image tile
            media_links.append(link['href'])
        elif re.search(r"https://bunkrrr.org/v/\w+", link['href']):  # Video tile
            media_links.append(link['href'])

    return media_links

def find_download_link(media_page_url):
    """Function to extract the download page link"""
    soup = get_soup(media_page_url)
    if not soup:
        return None
    
    # Find the download button URL (get.bunkrr.su/file pattern)
    for link in soup.find_all('a', href=True):
        if re.search(r"https://get\.bunkrr\.su/file/\d+", link['href']):
            return link['href']

    return None

def get_final_media_link(download_page_url):
    """Function to get the final media URL"""
    soup = get_soup(download_page_url)
    if not soup:
        return None

    # Find the final media download link, dynamic for any extension
    for link in soup.find_all('a', href=True):
        if re.search(r"https://.*\.(\w+)(\?download=true)?", link['href']):  # Dynamic for any extension
            return link['href']

    return None

def download_file(file_url, save_dir, retries=5):
    """Function to download the file with retries and resume functionality"""
    file_name = file_url.split("/")[-1]
    if "?download=true" in file_name:
        file_name = file_name.split("?")[0]  # Remove query parameters

    local_filename = os.path.join(save_dir, file_name)
    
    # Check if the file already exists and its size
    if os.path.exists(local_filename):
        resume_header = {"Range": f"bytes={os.path.getsize(local_filename)}-"}
        headers.update(resume_header)
    else:
        resume_header = None

    attempt = 0
    while attempt < retries:
        try:
            with requests.get(file_url, headers=headers, stream=True, timeout=60) as response:
                # Check if it's a resumable download
                if response.status_code == 206 and resume_header:
                    print(f"Resuming download for: {local_filename}")
                else:
                    print(f"Downloading: {local_filename}")
                
                with open(local_filename, 'ab') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:  # Filter out keep-alive chunks
                            f.write(chunk)
            print(f"Download complete: {local_filename}")
            return local_filename
        except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError, requests.exceptions.Timeout) as e:
            attempt += 1
            print(f"Error during download: {e}. Retrying {attempt}/{retries}...")
            time.sleep(5)  # Wait before retrying
        except Exception as e:
            print(f"Failed to download {file_url}: {e}")
            break

    print(f"Failed to download {file_url} after {retries} attempts.")
    return None

def ensure_unique_folder(base_folder, folder_name):
    """Ensure the folder name is unique by adding suffixes like ' - 2', ' - 3' if necessary"""
    folder_path = os.path.join(base_folder, folder_name)
    if not os.path.exists(folder_path):
        return folder_path

    # If folder exists, add a numerical suffix
    suffix = 2
    while os.path.exists(f"{folder_path} - {suffix}"):
        suffix += 1

    return f"{folder_path} - {suffix}"

def process_album(album_url, base_save_directory):
    """Process a single album to download all media"""
    soup = get_soup(album_url)
    album_title = extract_album_title(soup)

    # Create a unique subfolder for the album title inside the base directory
    album_save_directory = ensure_unique_folder(base_save_directory, album_title)
    os.makedirs(album_save_directory, exist_ok=True)

    # Step 1: Get all media links (images/videos) from the album page
    media_tile_links = find_media_links(album_url)
    
    if not media_tile_links:
        print(f"No media links found in album {album_url}")
        return

    # Step 2: Follow each media tile link and extract the download page URL
    for media_link in media_tile_links:
        download_link = find_download_link(media_link)
        if download_link:
            # Step 3: Get the final media URL from the download page
            final_media_url = get_final_media_link(download_link)
            if final_media_url:
                # Step 4: Download the file
                download_file(final_media_url, album_save_directory)
            else:
                print(f"Failed to get final media from {download_link}")
        else:
            print(f"Failed to find download link on {media_link}")

def main():
    # Check if a link was provided as a command line argument
    if len(sys.argv) < 2:
        print("Usage: python script.py <album_or_search_link>")
        sys.exit(1)

    url = sys.argv[1]  # Get the URL from the command line argument
    base_save_directory = "media_downloads"  # Default base directory

    # Determine the folder name based on search query
    if is_search_page(url):
        search_query = extract_search_query(url)
        save_directory = os.path.join(base_save_directory, search_query)
    else:
        # If it's a direct album link, name the folder based on the album title
        save_directory = base_save_directory

    # Create the directory if it doesn't exist
    os.makedirs(save_directory, exist_ok=True)

    # Check if the URL is a search result or a direct album link
    if is_search_page(url):
        print(f"Processing search results from {url}")
        # Get all album links from the search page
        album_links = find_album_links_from_search(url)
        
        if not album_links:
            print("No albums found in the search results.")
            return
        
        # Process each album found in the search results
        for album_link in album_links:
            print(f"Processing album {album_link}")
            process_album(album_link, save_directory)

    else:
        # Direct album link, process it
        print(f"Processing album {url}")
        process_album(url, save_directory)

if __name__ == "__main__":
    main()
