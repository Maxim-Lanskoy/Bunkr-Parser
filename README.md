# Bunkr Album & Media Downloader

This is a Python tool that downloads media from Bunkr albums and search results. It automatically handles albums and search results, downloads images and videos, and organizes them into folders named after the album titles or search queries.

## Features

- Supports downloading from direct Bunkr album links.
- Supports downloading media from search result pages.
- Automatically handles pagination for search results.
- Organizes downloaded media into folders based on album titles or search queries.
- Automatically appends numerical suffixes to folder names if they already exist (e.g., `Album Title`, `Album Title - 2`, etc.).
- Resumes partially downloaded files if interrupted.

## Prerequisites

Make sure you have Python 3 installed on your machine. You'll also need to install the following dependencies:

```bash
pip install requests beautifulsoup4 lxml
```

## Usage

### 1. Direct Album Download

To download media from a specific Bunkr album, run the script as follows:

```bash
python script.py "https://bunkrrr.org/a/mghxU8fP"
```

You can also omit the quotes if your URL does not contain special characters or spaces:

```bash
python script.py https://bunkrrr.org/a/mghxU8fP
```

The script will:
- Create a folder named after the album's title.
- Download all media files (videos and images) into that folder.

### 2. Download from Search Results

To download media from all albums found in a search result, run the script like this:

```bash
python script.py "https://bunkr-albums.io/?search=some%20video"
```

The script will:
- Create a folder named after the search query (e.g., `Some Video`).
- For each album found in the search results, it will download all media files into subfolders named after each album.

### 3. Folder Naming and Structure

- If a folder with the same name already exists, the script will append a numerical suffix to the folder name (e.g., `Album Title - 2`, `Album Title - 3`, etc.).
- The `media_downloads` folder will be the base directory where all files are downloaded, with subfolders for each album or search query.

### Example Commands

1. Download from a specific album:
   ```bash
   python script.py "https://bunkrrr.org/a/abcdefg"
   ```

2. Download from a search query with pagination:
   ```bash
   python script.py "https://bunkr-albums.io/?search=some%20video"
   ```

## Repository Structure

- **media_downloads/**: This is the default folder where media will be downloaded. You can customize this path if needed.
- **script.py**: This is the main script that handles downloading media from albums or search results.
