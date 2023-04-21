""" 
COMP 593 - Final Project

Description: 
  Downloads NASA's Astronomy Picture of the Day (APOD) from a specified date
  and sets it as the desktop background image.

Usage:
  python apod_desktop.py [apod_date]

Parameters:
  apod_date = APOD date (format: YYYY-MM-DD)
"""
from datetime import date
import hashlib
import os
import image_lib
import inspect
import sys
import re
import sqlite3

import apod_api

# Global variables
image_cache_dir = "images/"
image_cache_db = "images.db"

def main():
    ## DO NOT CHANGE THIS FUNCTION ##
    # Get the APOD date from the command line
    apod_date = get_apod_date()    

    # Get the path of the directory in which this script resides
    script_dir = get_script_dir()

    # Initialize the image cache
    init_apod_cache(script_dir)

    # Add the APOD for the specified date to the cache
    apod_id = add_apod_to_cache(apod_date)

    # Get the information for the APOD from the DB
    apod_info = get_apod_info(apod_id)

    # Set the APOD as the desktop background image
    if apod_id != 0:

        image_lib.set_desktop_background_image(apod_info['file_path'])

def get_apod_date():
    """Gets the APOD date
     
    The APOD date is taken from the first command line parameter.
    Validates that the command line parameter specifies a valid APOD date.
    Prints an error message and exits script if the date is invalid.
    Uses today's date if no date is provided on the command line.

    Returns:
        date: APOD date
    """
    args = sys.argv
    if len(args) < 2:
        # we need to validate date only if it is given by user 
        apod_date = date.today()
        return apod_date

    abort = False
    input_date = args[1]
    try:
        apod_date = date.fromisoformat(input_date)
    except ValueError as ex:
        print(ex)
        print(f"Error: Invalid date format; Invalid isoformat string: '{input_date}'")
        abort = True
    else:
        min_date_str = "1995-06-16"
        min_date = date.fromisoformat(min_date_str)
        if apod_date > date.today():
            print("Error: APOD date cannot be in the future")
            abort = True
        elif apod_date < min_date:
            print(f"Error: APOD date cannot be before: '{min_date_str}'")
            abort = True

    if abort == True:
        print("Script execution aborted")
        exit()
    return apod_date

def get_script_dir():
    """Determines the path of the directory in which this script resides

    Returns:
        str: Full path of the directory in which this script resides
    """
    ## DO NOT CHANGE THIS FUNCTION ##
    script_path = os.path.abspath(inspect.getframeinfo(inspect.currentframe()).filename)
    return os.path.dirname(script_path)

def init_apod_cache(parent_dir):
    """Initializes the image cache by:
    - Determining the paths of the image cache directory and database,
    - Creating the image cache directory if it does not already exist,
    - Creating the image cache database if it does not already exist.
    
    The image cache directory is a subdirectory of the specified parent directory.
    The image cache database is a sqlite database located in the image cache directory.

    Args:
        parent_dir (str): Full path of parent directory    
    """
    global image_cache_dir
    global image_cache_db

    completed_image_dir_path = os.path.join(parent_dir, image_cache_dir)
    print(f"Image cache directory: {completed_image_dir_path}")

    if os.path.exists(completed_image_dir_path):
        print("Image cache directory already exists.")
    else:
        os.mkdir(completed_image_dir_path)
        print("Image cache directory created.")

    # updated image cache dir
    image_cache_dir = completed_image_dir_path

    # create db connection i.e. if db is not present it will be automatically created
    complete_image_db_path = os.path.join(image_cache_dir, image_cache_db)
    print(f"Image cache DB: {complete_image_db_path}")

    already_exists = os.path.exists(complete_image_db_path)
    conn = sqlite3.connect(complete_image_db_path)

    if already_exists:
        print("Image cache DB already exists.")
    else:
        print("Image cache DB created.")

    cursor = conn.cursor()

    sql = """
        CREATE TABLE IF NOT EXISTS
            images (
                id INTEGER PRIMARY KEY,
                title VARCHAR,
                explanation VARCHAR,
                image_path VARCHAR,
                hash VARCHAR
            );
    """
    cursor.execute(sql)
    conn.commit()
    conn.close()

    # update cahce db path
    image_cache_db = complete_image_db_path
    return

def add_apod_to_cache(apod_date):
    """Adds the APOD image from a specified date to the image cache.
     
    The APOD information and image file is downloaded from the NASA API.
    If the APOD is not already in the DB, the image file is saved to the 
    image cache and the APOD information is added to the image cache DB.

    Args:
        apod_date (date): Date of the APOD image

    Returns:
        int: Record ID of the APOD in the image cache DB, if a new APOD is added to the
        cache successfully or if the APOD already exists in the cache. Zero, if unsuccessful.
    """
    print("APOD date:", apod_date.isoformat())

    global image_cache_dir
    apod_info = apod_api.get_apod_info(apod_date)
    if apod_info is None:
        print("Error: No APOD information for given date.")
        print("System execution aborted")
        exit()

    image_title = apod_info["title"]
    print(f"APOD title: {image_title}")

    image_url = apod_api.get_apod_image_url(apod_info)
    print(f"APOD URL: {image_url}")

    image_data = image_lib.download_image(image_url)
    if image_data is None:
        print("Error: Unable to download APOD image.")
        print("System execution aborted")
        exit()

    explanation = apod_info["explanation"]
    image_sha256 = _get_sha_of_image(image_data=image_data)
    print(f"APOD SHA-256: {image_sha256}")

    image_id = get_apod_id_from_db(image_sha256)
    if image_id != 0:
        print("APOD image is already in cache.")
    else:
        print("APOD image is not already in cache.")

        image_path = determine_apod_file_path(image_title, image_url)
        print(f"APOD file path: {image_path}")

        added = image_lib.save_image_file(image_path=image_path, image_data=image_data)

        # add in db only if image is added in directory
        if added:
            image_id = add_apod_to_db(title=image_title, explanation=explanation, file_path=image_path, sha256=image_sha256)
    
    return image_id

def add_apod_to_db(title, explanation, file_path, sha256):
    """Adds specified APOD information to the image cache DB.
     
    Args:
        title (str): Title of the APOD image
        explanation (str): Explanation of the APOD image
        file_path (str): Full path of the APOD image file
        sha256 (str): SHA-256 hash value of APOD image

    Returns:
        int: The ID of the newly inserted APOD record, if successful.  Zero, if unsuccessful       
    """
    global image_cache_db

    print("Adding APOD to image cache DB",end="...")
    conn = sqlite3.connect(image_cache_db)
    cursor = conn.cursor()
    sql = """
        insert into images (title, explanation, image_path, hash)
        values (?, ?, ?, ?);
    """
    variables = (title, explanation, file_path, sha256,)
    cursor.execute(sql, variables)
    try:
        conn.commit()
        apod_id = cursor.lastrowid
        print("success")
    except:
        print("failure")
        apod_id = 0
    conn.close()
    return apod_id

def get_apod_id_from_db(image_sha256):
    """Gets the record ID of the APOD in the cache having a specified SHA-256 hash value
    
    This function can be used to determine whether a specific image exists in the cache.

    Args:
        image_sha256 (str): SHA-256 hash value of APOD image

    Returns:
        int: Record ID of the APOD in the image cache DB, if it exists. Zero, if it does not.
    """
    
    conn = sqlite3.connect(image_cache_db)
    cursor = conn.cursor()
    sql = f"select id from images where hash = '{image_sha256}';"
    cursor.execute(sql)
    row = cursor.fetchone()
    conn.close()

    if row:
        apod_id = row[0]
    else:
        apod_id = 0
    return apod_id

def determine_apod_file_path(image_title: str, image_url):
    """Determines the path at which a newly downloaded APOD image must be 
    saved in the image cache. 
    
    The image file name is constructed as follows:
    - The file extension is taken from the image URL
    - The file name is taken from the image title, where:
        - Leading and trailing spaces are removed
        - Inner spaces are replaced with underscores
        - Characters other than letters, numbers, and underscores are removed

    For example, suppose:
    - The image cache directory path is 'C:\\temp\\APOD'
    - The image URL is 'https://apod.nasa.gov/apod/image/2205/NGC3521LRGBHaAPOD-20.jpg'
    - The image title is ' NGC #3521: Galaxy in a Bubble '

    The image path will be 'C:\\temp\\APOD\\NGC_3521_Galaxy_in_a_Bubble.jpg'

    Args:
        image_title (str): APOD title
        image_url (str): APOD image URL
    
    Returns:
        str: Full path at which the APOD image file must be saved in the image cache directory
    """
    global image_cache_dir

    # get extention of image
    image_ext = image_url.split(".")[-1]
    
    # remove space from front and end of title
    image_title = image_title.strip()

    # convert space into underscore
    image_title = image_title.replace(" ", "_")

    # consider only alphabers, numbers or underscore in image title
    image_title = re.sub(r"[^a-zA-Z0-9_]", "", image_title)

    # create file name using title and extension
    file_name = image_title + "." + image_ext

    # create complete file path
    file_path = os.path.join(image_cache_dir, file_name)
    return file_path

def get_apod_info(image_id):
    """Gets the title, explanation, and full path of the APOD having a specified
    ID from the DB.

    Args:
        image_id (int): ID of APOD in the DB

    Returns:
        dict: Dictionary of APOD information
    """
    global image_cache_db

    conn = sqlite3.connect(image_cache_db)
    cursor = conn.cursor()
    sql = "select title, explanation, image_path from images where id = ?;"
    cursor.execute(sql, (image_id,))
    row = cursor.fetchone()

    apod_info = {
        'title': row[0],
        'explanation': row[1],
        'file_path': row[2],
    }
    conn.close()
    return apod_info

def _get_sha_of_image(image_data):
    return hashlib.sha256(image_data).hexdigest()

def get_all_apod_titles():
    """Gets a list of the titles of all APODs in the image cache

    Returns:
        list: Titles of all images in the cache
    """
    # TODO: Complete function body
    # NOTE: This function is only needed to support the APOD viewer GUI
    return

if __name__ == '__main__':
    main()
