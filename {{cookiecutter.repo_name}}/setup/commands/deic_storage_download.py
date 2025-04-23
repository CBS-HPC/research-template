import requests
import subprocess
import re
import os
import urllib.parse
import multiprocessing
import argparse
import sys

import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from utils import *


pip_installer(required_libraries = ['beautifulsoup4'] )
from bs4 import BeautifulSoup

def links_deic_storage(url):
    """
    Prints all the links (URLs) found in the given web page URL.

    Parameters:
        url (str): The URL of the web page to scan for links.
    """
    try:
        # Send a GET request to the URL
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the HTML content of the page
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all anchor tags with 'href' attribute
            links = soup.find_all('a', href=True)
            
            return links
           
        else:
            print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
            return None
    except Exception as e:
        return None

def extract_file_paths(html_contents):
    # Regular expression pattern to match file paths starting with "/share_redirect/"
    pattern = r'/share_redirect/[^\s<>"]+'
    file_paths  =[]
    # Loop through each element in the ResultSet (html_contents)
    for element in html_contents:
        # Get the 'href' attribute from the anchor tag
        href = element.get('href')
        
        if href:
            # Find all matches for file paths starting with "/share_redirect/"
            path = re.findall(pattern, href)
            if path: 
                file_paths.append(path[0])
    return file_paths

def download_file_worker(file_path, save_dir):
    """ Worker function for downloading a single file """
    print(f"Downloading file from: {file_path}")
    
    # Construct the full URL to the file
    full_url = "https://sid.storage.deic.dk" + file_path
    
    # Extract the file name from the URL (the part after the last '/')
    file_name = os.path.basename(urllib.parse.unquote(full_url))  # Decode URL-encoded characters

    # Create the full path by joining the directory and file name
    save_path = os.path.join(save_dir, file_name)

    try:
        # Send a GET request to download the file content
        response = requests.get(full_url, stream=True)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Write the content to the file in binary mode
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):  # Stream in chunks to avoid memory overload
                    f.write(chunk)
    except Exception as e:
        print(f"Error downloading {full_url}: {e}")

def download_files_parallel(file_paths, save_dir, n_workers):
    """ Parallelizes the download of multiple files using multiprocessing """

    # Ensure the directory exists
    os.makedirs(save_dir, exist_ok=True)

    if n_workers > 1:
        # Create a pool of workers to download the files in parallel
        with multiprocessing.Pool(processes=n_workers) as pool:
            # Map the worker function to each file_path
            pool.map(download_file_worker, [(path, save_dir) for path in file_paths])
    else:
        # Fallback to sequential download if only one worker
        for path in file_paths:
            download_file_worker(path, save_dir)

@ensure_correct_kernel
def deic_storage_download(link, save_dir, n_workers=1):
    """ Download files from the given link using parallel workers or sequentially """
    links = links_deic_storage(link)
    file_paths = extract_file_paths(links)
    download_files_parallel(file_paths, save_dir, n_workers)

def main():
    # Command-line argument parser
    parser = argparse.ArgumentParser(description="Set data source and monitor file creation.")
    parser.add_argument("remote_path", help="URL link to the dataset")
    parser.add_argument("destination", help="Path where data will be stored")
    args = parser.parse_args()
    
    deic_storage_download(args.remote_path, args.destination)
  

if __name__ == "__main__":
    main()

#link = "https://sid.storage.deic.dk/cgi-sid/ls.py?share_id=CyOR8W3h2f"

#dropbox = "https://www.dropbox.com/scl/fo/ro7vwy40ym5zoi2z7kbxs/AORJDfZ2lolBz2J2Tf02iYQ?rlkey=1urgvvvy722b8ci1dwdyd6jbg&st=9g1kd9ah&dl=0"

#raw_data = "C:/Users/kgp.lib/OneDrive - CBS - Copenhagen Business School/Desktop/Ny mappe/test_0001241/data/raw"

#deic_storage_download(link,raw_data)