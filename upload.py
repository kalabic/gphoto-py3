#gphotoup
#Simple but flexible script to upload photos to Google Photos. 
#Useful if you have photos in a directory structure 
#that you want to reflect as Google Photos albums.

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
import json
import os
import os.path
import argparse
import logging
import re
from pprint import pprint
from pathlib import Path

#TODO:
# 1. Support cron run 
# 2. Enhance support for uploading specific folder/specefic file 


def parse_args(arg_input=None):
    parser = argparse.ArgumentParser(description='Upload photos to Google Photos.')
    parser.add_argument('--auth ', metavar='auth_file', dest='auth_file', default='auth/auth.txt',
                    help='file for reading/storing user authentication tokens')
    parser.add_argument('--path ', metavar='root_folder', dest='root_folder', default='.',
                    help='path to root of album album folders')                
    parser.add_argument('--album', metavar='album_name', dest='album_name',
                    help='name of photo album to create (if it doesn\'t exist). Any uploaded photos will be added to this album.')
    parser.add_argument('--log', metavar='log_file', dest='log_file',
                    help='name of output file for log messages')
    parser.add_argument('--up',dest='run_upload', action='store_true',
                    help='run upload to  gphoto')                
    parser.add_argument('--ls',dest='albums_list', action='store_true',
                    help='list all albums in gphoto')
    parser.add_argument('--exclude', metavar='exclude', dest='exclude',
                    help='regex to exclude')                    
    parser.add_argument('photos', metavar='photo',type=str, nargs='*',
                    help='filename of a photo to upload')
    return parser.parse_args(arg_input)


def auth(scopes):
    flow = InstalledAppFlow.from_client_secrets_file(
        'auth/client_id.json',
        scopes=scopes)
    
    credentials = flow.run_console()
    return credentials

def get_authorized_session(auth_token_file):

    scopes=['https://www.googleapis.com/auth/photoslibrary',
            'https://www.googleapis.com/auth/photoslibrary.sharing']

    cred = None

    if auth_token_file:
        try:
            cred = Credentials.from_authorized_user_file(auth_token_file, scopes)
        except OSError as err:
            logging.debug("Error opening auth token file - {0}".format(err))
        except ValueError:
            logging.debug("Error loading auth tokens - Incorrect format")


    if not cred:
        cred = auth(scopes)
        #save credentials for next time
        save_cred(cred,auth_token_file)	

    session = AuthorizedSession(cred)

    if auth_token_file:
        try:
            save_cred(cred, auth_token_file)
        except OSError as err:
            logging.debug("Could not save auth tokens - {0}".format(err))

    return session


def save_cred(cred, auth_file):

    cred_dict = {
        'token': cred.token,
        'refresh_token': cred.refresh_token,
        'id_token': cred.id_token,
        'scopes': cred.scopes,
        'token_uri': cred.token_uri,
        'client_id': cred.client_id,
        'client_secret': cred.client_secret
    }

    with open(auth_file, 'w') as f:
        print(json.dumps(cred_dict), file=f)

# Generator to loop through all albums
def getAlbums(session, appCreatedOnly=False):

    params = {
            'excludeNonAppCreatedData': appCreatedOnly
    }

    while True:

        albums = session.get('https://photoslibrary.googleapis.com/v1/albums', params=params).json()

        logging.debug("Server response: {}".format(albums))

        if 'albums' in albums:

            for a in albums["albums"]:
                yield a

            if 'nextPageToken' in albums:
                params["pageToken"] = albums["nextPageToken"]
            else:
                return

        else:
            return


def create_or_retrieve_album(session, album_title):

    # Find albums created by this app to see if one matches album_title
    for a in getAlbums(session, True):
        if a["title"].lower() == album_title.lower():
            album_id = a["id"]
            logging.info("Uploading into EXISTING photo album -- \'{0}\'".format(album_title))
            return album_id

    # No matches, create new album
    create_album_body = json.dumps({"album":{"title": album_title}})
    #print(create_album_body)
    resp = session.post('https://photoslibrary.googleapis.com/v1/albums', create_album_body).json()

    logging.debug("Server response: {}".format(resp))

    if "id" in resp:
        logging.info("Uploading into NEW photo album -- \'{0}\'".format(album_title))
        return resp['id']
    else:
        logging.error("Could not find or create photo album '\{0}\'. Server Response: {1}".format(album_title, resp))
        return None


def upload_photos(session, photo_file_list, album_name):

    album_id = create_or_retrieve_album(session, album_name) if album_name else None


    # interrupt upload if an upload was requested but could not be created
    if album_name and not album_id:
        return

    files_list = list(getAlbumContent(session,album_id)) 
    # for item in files_list:
    #      pprint(item)


    session.headers["Content-type"] = "application/octet-stream"
    session.headers["X-Goog-Upload-Protocol"] = "raw"

    for photo_file_name in photo_file_list:

            #if file with this name already exists
            #don't upload it  
            if os.path.basename(photo_file_name) in files_list:
                logging.info("Skipping photo(already exist in album) -- \'{}\'".format(photo_file_name))
                continue
            try:
                photo_file = open(photo_file_name, mode='rb')
                photo_bytes = photo_file.read()
            except OSError as err:
                logging.error("Could not read file \'{0}\' -- {1}".format(photo_file_name, err))
                continue

   
            session.headers["X-Goog-Upload-File-Name"] = os.path.basename(photo_file_name)

            logging.info("Uploading photo -- \'{}\'".format(photo_file_name))

            #upload item 
            upload_token = session.post('https://photoslibrary.googleapis.com/v1/uploads', photo_bytes)

            if (upload_token.status_code == 200) and (upload_token.content):

                create_body = json.dumps({"albumId":album_id, "newMediaItems":[{"description":"","simpleMediaItem":{"uploadToken":upload_token.content.decode()}}]}, indent=4)
                # add item to album
                resp = session.post('https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate', create_body).json()

                logging.debug("Server response: {}".format(resp))

                if "newMediaItemResults" in resp:
                    status = resp["newMediaItemResults"][0]["status"]
                    if status.get("code") and (status.get("code") > 0):
                        logging.error("Could not add \'{0}\' to library -- {1}".format(os.path.basename(photo_file_name), status["message"]))
                    else:
                        logging.info("Added \'{}\' to library and album \'{}\' ".format(os.path.basename(photo_file_name), album_name))
                else:
                    logging.error("Could not add \'{0}\' to library. Server Response -- {1}".format(os.path.basename(photo_file_name), resp))

            else:
                logging.error("Could not upload \'{0}\'. Server Response - {1}".format(os.path.basename(photo_file_name), upload_token))

    try:
        del(session.headers["Content-type"])
        del(session.headers["X-Goog-Upload-Protocol"])
        del(session.headers["X-Goog-Upload-File-Name"])
    except KeyError:
        pass


def getFilesInFolder(folder_path,exclude):

    #gphotos can only deal with (according to docs):
    #Photos:	BMP, GIF, HEIC, ICO, JPG, PNG, TIFF, WEBP, some RAW files.	200 MB
    #Videos:	3GP, 3G2, ASF, AVI, DIVX, M2T, M2TS, M4V, MKV, MMV, MOD, MOV, MP4, MPG, MTS, TOD, WMV.	10 GB

    regex = r'\.(BMP|GIF|HEIC|ICO|JPG|PNG|TIFF|WEBP|RAW|3GP|3G2|ASF|AVI|DIVX|M2T|M2TS|M4V|MKV|MMV|MOD|MOV|MP4|MPG|MTS|TOD|WMV)$'
    result = []
    for file in list(Path(folder_path).rglob("*")):
        if not (exclude and re.search(exclude, str(file),re.IGNORECASE)): 
            if file and re.search(regex, str(file),re.IGNORECASE):
                result.append(file)

    return result


def getFolderList(root_path):
    #one level under root is list of our albums
    result = next(os.walk(root_path))[1]
    return result    


def uploadToAlbums(session, root_path, exclude):
    album_list = getFolderList(root_path)
    for album in album_list:
        files = getFilesInFolder(root_path + '/' + album, exclude )
        if files:
            upload_photos(session, files, album)


def getAlbumContent(session,album_id):
    params = {
         #'excludeNonAppCreatedData': appCreatedOnly
        "pageSize": "100",
        "albumId": album_id
    }

    while True:
        resp = session.post('https://photoslibrary.googleapis.com/v1/mediaItems:search', params=params).json()

        logging.debug("Server response: {}".format(resp))

        if 'mediaItems' in resp:

            for a in resp["mediaItems"]:
                yield a['filename']

            if 'nextPageToken' in resp:
                params["pageToken"] = resp["nextPageToken"]
            else:
                return

        else:
            return


def printAlbums(session):
    print("{:<50} | {:>8} | {} ".format("PHOTO ALBUM","# PHOTOS", "IS WRITEABLE?"))

    for a in getAlbums(session):
        print("{:<50} | {:>8} | {} ".format(a["title"],a.get("mediaItemsCount", "0"), str(a.get("isWriteable", False))))


def main():

    args = parse_args()

    logging.basicConfig(format='%(asctime)s %(module)s.%(funcName)s:%(levelname)s:%(message)s',
                    datefmt='%m/%d/%Y %I_%M_%S %p',
                    filename=args.log_file,
                    level=logging.INFO)

    session = get_authorized_session(args.auth_file)
    if args.run_upload == True:
        uploadToAlbums(session, args.root_folder, args.exclude)

    # As a quick status check, dump the albums and their key attributes
    if args.albums_list == True:
        printAlbums(session)

   
if __name__ == '__main__':
  main()
