'''
Library for interacting with NASA's Astronomy Picture of the Day API.
'''

import requests
import urllib

import apod_desktop

APOD_API_KEY = "py71Ph75zvHlT30BVVx4tumErRWYJwjaK3Gntrha"
APOD_API_URL = f"https://api.nasa.gov/planetary/apod?api_key={APOD_API_KEY}&date="

def main():
    # NOTE: needed to validate date so used apod_desktop.get_apod_date function
    # instead of replication the code. 
    apod_date = apod_desktop.get_apod_date()
    apod_info = get_apod_info(apod_date)
    if apod_info is None:
        print("Error: No APOD information for given date.")
        print("System execution aborted")
        exit()

    import json
    print(json.dumps(apod_info))

    image_url = get_apod_image_url(apod_info)
    print("Success: image url is: ",image_url)
    return

def get_apod_info(apod_date):
    """Gets information from the NASA API for the Astronomy 
    Picture of the Day (APOD) from a specified date.

    Args:
        apod_date (date): APOD date (Can also be a string formatted as YYYY-MM-DD)

    Returns:
        dict: Dictionary of APOD info, if successful. None if unsuccessful
    """
    iso_apod_date = apod_date.isoformat()
    print(f"Getting {iso_apod_date} APOD information from NASA...",end="")
    apod_url = APOD_API_URL + iso_apod_date
    response = requests.get(apod_url)
    if response.status_code == 200:
        print("success")
        return response.json()
    print("failure")
    return None

def get_apod_image_url(apod_info_dict):
    """Gets the URL of the APOD image from the dictionary of APOD information.

    If the APOD is an image, gets the URL of the high definition image.
    If the APOD is a video, gets the URL of the video thumbnail.

    Args:
        apod_info_dict (dict): Dictionary of APOD info from API

    Returns:
        str: APOD image URL
    """
    # # NOTE: "hdurl" doesn't works sometimes
    # return apod_info_dict["hdurl"]
    media_type = apod_info_dict["media_type"]
    if media_type == "video":
        video_url = apod_info_dict["url"]
        url = _get_thumbnail_url(video_url)
    elif media_type == "image":
        url = apod_info_dict["url"]
    else:
        url = ""
    return url

def _get_thumbnail_url(video_url):
    path = urllib.parse.urlparse(video_url).path
    if path.startswith("/embed/"):
        # remove "/embed" from path
        path = path[7:]

    # what remains in "path" is the video-id
    thumbnail_url = f"https://img.youtube.com/vi/{path}/hqdefault.jpg"
    return thumbnail_url

if __name__ == '__main__':
    main()