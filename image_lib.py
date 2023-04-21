'''
Library of useful functions for working with images.
'''
import ctypes
import sys
import os
import requests


def main():
    args = sys.argv
    if len(args) < 3:
        print("Error: Please provide image url and image path to save image.")
        print("Script execution aborted")
        exit()

    image_url = args[1]
    image_path = args[2]
    image = download_image(image_url)
    if image is None:
        print("Error: Invalid image url.")
        print("Script execution aborted")
        exit()

    # image_path = os.path.join(image_dir, "")
    added = save_image_file(image_data=image, image_path=image_path)
    if not added:
        print("Error: Image not saved in given file path.")
    else:
        print("Image saved in given file path")
    return

def download_image(image_url):
    """Downloads an image from a specified URL.

    DOES NOT SAVE THE IMAGE FILE TO DISK.

    Args:
        image_url (str): URL of image

    Returns:
        bytes: Binary image data, if succcessful. None, if unsuccessful.
    """
    print(f"Downloading image from\n{image_url}",end="...")
    response = requests.get(image_url)
    if response.status_code == 200:
        print("success")
        return response.content
    print("failure")
    return None

def save_image_file(image_data, image_path):
    """Saves image data as a file on disk.
    
    DOES NOT DOWNLOAD THE IMAGE.

    Args:
        image_data (bytes): Binary image data
        image_path (str): Path to save image file

    Returns:
        bytes: True, if succcessful. False, if unsuccessful
    """
    print(f"Saving image file as {image_path}",end="...")
    try:
        with open(image_path, "wb") as file:
            file.write(image_data)
            file.close()
        print("success")
        return True
    except:
        print("failure")
        return False

def set_desktop_background_image(image_path):
    """Sets the desktop background image to a specific image.

    Args:
        image_path (str): Path of image file

    Returns:
        bytes: True, if succcessful. False, if unsuccessful        
    """
    print(f"Setting desktop to {image_path}",end="...")
    try:
        ctypes.windll.user32.SystemParametersInfoA(20, 0, image_path, 3)
        print("success")
    except:
        print("failure")
    return

def scale_image(image_size, max_size=(800, 600)):
    """Calculates the dimensions of an image scaled to a maximum width
    and/or height while maintaining the aspect ratio  

    Args:
        image_size (tuple[int, int]): Original image size in pixels (width, height) 
        max_size (tuple[int, int], optional): Maximum image size in pixels (width, height). Defaults to (800, 600).

    Returns:
        tuple[int, int]: Scaled image size in pixels (width, height)
    """
    ## DO NOT CHANGE THIS FUNCTION ##
    # NOTE: This function is only needed to support the APOD viewer GUI
    resize_ratio = min(max_size[0] / image_size[0], max_size[1] / image_size[1])
    new_size = (int(image_size[0] * resize_ratio), int(image_size[1] * resize_ratio))
    return new_size

if __name__ == '__main__':
    main()