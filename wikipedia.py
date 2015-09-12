import bs4
import os
import requests
import shutil
import time

import mongodb

DOWNLOAD_PATH = '/home/ubuntu/images'
SPECIES_DB = 'speciesdb'
SPECIES_COLLECTION = 'species'
IMAGE_DB = 'imagedb'
WIKIPEDIA_URL = 'https://en.wikipedia.org/wiki'
WIKIPEDIA_API_URL = 'https://commons.wikimedia.org/w/api.php?'
DELAY_CONSTANT = 3


def download_image(image_url, download_path):
    """Download an image from a url

    :param image_url:       The url of the image to download
    :param download_path:   The local file path for the image

    :returns:               True if download successful; False otherwise

    """
    response = requests.get(image_url, stream=True)
    time.sleep(DELAY_CONSTANT)
    if response.status_code != requests.codes.ok:
        return False

    with open(download_path, 'wb') as outfile:
        shutil.copyfileobj(response.raw, outfile)
    del response
    return True


def get_image_meta(filename, image_source):
    """Get the image meta for an image in Wikipedia Commons

    :param filename:        Name of the file in Wikipedia Commons
    :param image_source     URL of the file in Wikipedia Commons

    :returns:               A dict of the form
                                {'artist': ...,
                                 'credit': ...,
                                 'permission': ...,
                                 'usage_terms': ...,
                                 'filename': ...,
                                 'source': ...}
                            None if the file is not found, the file does not
                                contain metadata, or there is a processing
                                error

    """
    params = {'action': 'query',
              'prop': 'imageinfo',
              'format': 'json',
              'iiprop': 'extmetadata',
              'iilimit': 1,
              'titles': 'File:{0}'.format(filename)}

    response = requests.get(WIKIPEDIA_API_URL, params=params)
    time.sleep(DELAY_CONSTANT)
    if response.status_code != requests.codes.ok:
        return None
    response = response.json()

    try:
        image_data = response['query']['pages'].values()[0]['imageinfo'][0][
            'extmetadata']
    except KeyError:
        return None

    image_meta = {'Artist': '',
                  'Credit': '',
                  'Permission': '',
                  'UsageTerms': ''}
    for key in image_meta:
        try:
            value = image_data[key]['value']
            image_meta[key] = bs4.BeautifulSoup(value).getText().strip()
        except KeyError:
            pass

    image_meta = {'artist': image_meta['Artist'],
                  'credit': image_meta['Credit'],
                  'permission': image_meta['Permission'],
                  'usage_terms': image_meta['UsageTerms'],
                  'filename': filename,
                  'source': image_source}
    return image_meta


def get_taxobox_image(page_title):
    """Get the filename and url location of the taxobox image for a wikipedia
    page

    :param page_title:      Title of the page to search

    :return:                A tuple of (filename, image_src), where filename
                                is the name of the image file and image_src
                                is the url location of the image in Wikipedia
                                Commons.
                            None, None if the Wikipedia page does not contain
                                a taxobox, the taxobox does not contain a main
                                image, or there is a processing error

    """
    url = "/".join([WIKIPEDIA_URL, page_title])

    response = requests.get(url)
    time.sleep(DELAY_CONSTANT)
    if response.status_code != requests.codes.ok:
        return None

    soup = bs4.BeautifulSoup(response.content)

    try:
        taxobox = soup.find("table", {"class":"infobox biota"})
        cell = taxobox.find("td")
        link = cell.find("a", {"class": "image"})
        img = link.find("img")
        filename = img.get("alt")
        image_src = img.get("src")
    except (AttributeError, IndexError):
        return None, None
    return filename, image_src

    
def __main__():
    species_list = ['Corvus corax', 'Poecile gambeli', 'Sialia mexicana',
                    'Aphelocoma californica', 'Gymnogyps californianus',
                    'Junco hyemalis', 'Sitta carolinensis']
    
    mongocon = mongodb.MongoDBConnection()
    for species in species_list:
        filename, image_src = get_taxobox_image(species)
        if filename is None or image_src is None:
            mongocon.set_image_id(species, None)
            mongocon.set_image_meta(species, None)
            print 'NO IMAGE: ' + species
            continue

        image_meta = get_image_meta(filename, image_src)
        if image_meta is None:
            mongocon.set_image_id(species, None)
            mongocon.set_image_meta(species, None)
            print 'NO IMAGE META: ' + species
            continue

        name, extension = os.path.split(image_src)
        filename = '.'.join([species, extension])
        download_path = '/'.join([DOWNLOAD_PATH, filename])
        if not download_image(image_src, download_path):
            mongocon.set_image_id(species, None)
            mongocon.set_image_meta(species, None)
            print 'NO IMAGE: ' + species
            continue

        image_id = mongocon.insert_image(download_path, filename)
        mongocon.set_image_meta(species, image_meta)
        mongocon.set_image_meta(species, image_id)
        print 'IMAGE FOUND: ' + species