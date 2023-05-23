#gphotoup
#Simple but flexible script to upload photos to Google Photos. 
#Useful if you have photos in a directory structure 
#that you want to reflect as Google Photos albums.

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
from datetime import datetime
import json
import os
import os.path
import argparse
import logging
import re
import sys
from pprint import pprint
from pathlib import Path

#TODO:
# 1. Support cron run 
# 2. Enhance support for uploading specific folder/specefic file 


def parse_args(arg_input=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''\
Upload photos to Google Photos. Run first time with 'auth' argument to
create auth token, update your client id and secret in 'auth/client_id.json'.
Auth is saved into 'auth/token.json' and 'auth' argument is not needed
any more.

Examples:
  Create auth token: gphoto.py --auth
     Upload a photo: gphoto.py --up --album myalbum myphoto.jpeg
    List all albums: gphoto.py --ls
List items in album: gphoto.py --ls --album myalbum

''')
    parser.add_argument('--auth ', dest='create_auth', action='store_true',
                    help="Create authentication token if it does not exist, or try to load it and exit.")
    parser.add_argument('--clientid', metavar='client_id_file', dest='client_id_file',
                    help="File where client id and secret is stored. Used in combination with '--auth'. (optional, default is 'auth/client_id.json'")
    parser.add_argument('--token', metavar='token_file', dest='token_file',
                    help="File where authentication token is stored. (optional, default is 'auth/token.json'")
#    parser.add_argument('--path ', metavar='root_folder', dest='root_folder', default='.',
#                    help="Path to root of album album folders.")
    parser.add_argument('--album', metavar='album_name', dest='album_name',
                    help="Name of photo album to create (if it doesn't exist). Any uploaded photos will be added to this album.")
    parser.add_argument('--log', metavar='log_file', dest='log_file',
                    help="Name of output file for log messages.")
    parser.add_argument('--up',dest='run_upload', action='store_true',
                    help="Run upload to gphoto.")
    parser.add_argument('--ls',dest='albums_list', action='store_true',
                    help="List all albums in gphoto. Combination with '--album' will list all items in album.")
#    parser.add_argument('--exclude', metavar='exclude', dest='exclude',
#                    help="Regex to exclude.")
    parser.add_argument('photos', metavar='photo',type=str, nargs='*',
                    help="filename of a photo to upload")
    return parser.parse_args(arg_input)


def auth(client_id_file, scopes):
    flow = InstalledAppFlow.from_client_secrets_file(
        client_id_file,
        scopes=scopes)
    
    credentials = flow.run_local_server(host='localhost',
                                        port=8080,
                                        authorization_prompt_message="",
                                        success_message='The auth flow is complete; you may close this window.',
                                        open_browser=True)

    return credentials


def get_authorized_session(client_id_file, token_file):
    scopes=['https://www.googleapis.com/auth/photoslibrary',
            'https://www.googleapis.com/auth/photoslibrary.sharing',
            'https://www.googleapis.com/auth/photoslibrary.edit.appcreateddata']

    cred = None

    try:
        cred = Credentials.from_authorized_user_file(token_file,scopes)
    except OSError as err:
        logging.debug("Error opening auth token file - {0}".format(err))
    except ValueError:
        logging.debug("Error loading auth tokens - Incorrect format")

    # Create session and return if saved credentials already exist.
    if cred is not None:
        session = AuthorizedSession(cred)
        return session
        
    try:
        # If saved credentials do not exist, try to create them and save for later.
        cred = auth(client_id_file, scopes)
        
        save_cred(cred, token_file)
        
    except OSError as err:
        logging.error("Could not load/save auth tokens - {0}".format(err))
        return None

    session = AuthorizedSession(cred)
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

        try:
            albums = session.get('https://photoslibrary.googleapis.com/v1/albums', params=params).json()
        except (RefreshError) as err:
            # Relevant for this error: https://stackoverflow.com/a/59202851/852428
            logging.error("google.auth.exception - RefreshError - {0}".format(err))
            print("NOTE: When RefreshError happens you likely need to delete and request token again.")
            return None
        except OSError as err:
            logging.error("Failed to list albums - {0}".format(err))
            return None

        if 'albums' in albums:
            logging.debug("Server response: {}".format(albums))

            for a in albums["albums"]:
                yield a

            if 'nextPageToken' in albums:
                params["pageToken"] = albums["nextPageToken"]
            else:
                return

        elif "error" in albums:
            error = albums["error"]
            if "code" in error and "message" in error and "status" in error:
                logging.debug("Server response: {}".format(albums))
                print("error: {}; {}; {}".format(error["code"], error["status"], error["message"]))
            else:
                logging.error("Server response: {}".format(albums))
                
            return None
        
        else:
            return

def getAlbumId(session, album_name, app_created_only=False):

    params = {
            'excludeNonAppCreatedData': app_created_only
    }

    while True:

        albums = session.get('https://photoslibrary.googleapis.com/v1/albums', params=params).json()

        if 'albums' in albums:
            logging.debug("Server response: {}".format(albums))

            for a in albums["albums"]:
                if a["title"] == album_name:
                    return a["id"]

            if 'nextPageToken' in albums:
                params["pageToken"] = albums["nextPageToken"]
            else:
                return

        elif "error" in albums:
            error = albums["error"]
            if "code" in error and "message" in error and "status" in error:
                logging.debug("Server response: {}".format(albums))
                print("error: {}; {}; {}".format(error["code"], error["status"], error["message"]))
            else:
                logging.error("Server response: {}".format(albums))
                
            return None

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
    elif "error" in resp:
        error = resp["error"]
        if "code" in error and "message" in error and "status" in error:
            logging.debug("Could not find or create photo album '\{0}\'. Server Response: {1}".format(album_title, resp))
            print("error: {}; {}; {}".format(error["code"], error["status"], error["message"]))
        else:
            logging.error("Could not find or create photo album '\{0}\'. Server Response: {1}".format(album_title, resp))
        return None
    else:
        logging.error("Could not find or create photo album '\{0}\'. Server Response: {1}".format(album_title, resp))
        return None


def upload_photos(session, photo_file_list, album_name):

    album_id = create_or_retrieve_album(session, album_name) if album_name else None


    # interrupt upload if an upload was requested but could not be created
    if album_name and not album_id:
        return False

    # Get album content
    existing_files_list = list(getAlbumContent(session,album_id)) 

    session.headers["Content-type"] = "application/octet-stream"
    session.headers["X-Goog-Upload-Protocol"] = "raw"

    for photo_file_name_unsafe in photo_file_list:

            photo_file_name = photo_file_name_unsafe.encode(encoding = 'UTF-8', errors = 'strict')
            # For debugging Unicode: print("PHOTO FILE NAME: {}".format(photo_file_name))

            #if file with this name already exists in this album
            #don't upload it  
            if os.path.basename(photo_file_name) in existing_files_list:
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
                        productUrl = resp["newMediaItemResults"][0]["mediaItem"]["productUrl"]
                        filename = resp["newMediaItemResults"][0]["mediaItem"]["filename"]
                        print("{} URL: {}".format(filename,productUrl))

                    # Insert creation time into item description
                    try:
                        creation_date = getFileCreationDate(photo_file_name)
                        descr = album_name + ' @' + creation_date 
                        setDescription(session, resp["newMediaItemResults"][0]["mediaItem"]["id"], descr)
                    except ValueError as exp:
                        print ("Error", exp) 
                    ####    
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
        
    return True

# returns string containing the file's creation date
def getFileCreationDate(file_path):
    try:
        stat = os.stat(file_path)
    except OSError as err:
        logging.error("Could not get stat for  \'{0}\' -- {1}".format(file_path, err))
        raise ValueError("Can't get stat for file")

    early_time = min(stat.st_atime,stat.st_mtime,stat.st_ctime)
    if early_time == 0:
         raise ValueError("File has 0 creation time")
    res=datetime.fromtimestamp(early_time).strftime("%Y-%m-%d %H:%M:%S")
    return res    


#set description to file
def setDescription(session, media_item_id, description):
    params = {
        'updateMask': 'description'
    }
    url = 'https://photoslibrary.googleapis.com/v1/mediaItems/' + media_item_id

    # Unfortunetely API doesn't allow to change creation time.
    create_body = json.dumps( { "description": description ,
                                #"mediaMetadata": { "creationTime":"2014-10-02T15:01:23Z"}
                              }, 
                              indent=4)
    resp = session.patch(url, params=params,data=create_body).json()
    #print(resp)

    



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

def printAlbumContent(session,album_name):

    album_id = getAlbumId(session,album_name)

    if album_id == None:
        print("Album not found: {}".format(album_name))
        return False

    params = {
         #'excludeNonAppCreatedData': appCreatedOnly
        "pageSize": "100",
        "albumId": album_id
    }

    print("{:<40} | {:>8}".format("FILE NAME","DESCRIPTION"))

    while True:
        resp = session.post('https://photoslibrary.googleapis.com/v1/mediaItems:search', params=params).json()

        logging.debug("Server response: {}".format(resp))

        if 'mediaItems' in resp:

            for a in resp["mediaItems"]:
                if "filename" in a:
                    if "description" in a:
                        print("{:<40} | {:>8}".format(a["filename"], a["description"]))
                    else:
                        print("{:<40} |".format(a["filename"]))
                else:
                    print("{:<40} |".format("????"))

            if 'nextPageToken' in resp:
                params["pageToken"] = resp["nextPageToken"]
            else:
                return True

        else:
             # TODO: Check this
            return True


def printAlbums(session):
    print("{:<50} | {:>8} | {} ".format("PHOTO ALBUM","# PHOTOS", "IS WRITEABLE?"))

    for a in getAlbums(session):
        print("{:<50} | {:>8} | {} ".format(a["title"],a.get("mediaItemsCount", "0"), str(a.get("isWriteable", False))))


def main():

    args = parse_args()

    action_count = 0
    if args.create_auth == True:
        action_count += 1

    if args.albums_list == True:
        action_count += 1

    if args.run_upload == True:
        action_count += 1

    if action_count == 0:
        print("Run 'gphoto.py -h' for help.")
        sys.exit(1)

    if action_count != 1:
        print("error: Multiple actions specified")
        sys.exit(1)

    logging.basicConfig(format='%(asctime)s %(module)s.%(funcName)s:%(levelname)s:%(message)s',
                    datefmt='%m/%d/%Y %I_%M_%S %p',
                    filename=args.log_file,
                    level=logging.INFO)

    # Default paths are relative to python script. Paths in arguments are relative to current directory of execution in command line.
    client_id_file = sys.path[0] + "/auth/client_id.json";
    token_file = sys.path[0] + "/auth/token.json";

    #
    # Begin validation of given arguments.
    #

    # If client_id_file argument is given, warn that it is used only during authentication action.
    if args.create_auth == False and args.client_id_file is not None:
        print("warning: argument 'clientid' is used only with 'auth'")

    # If client_id_file argument is given for authentication action, file must exist.
    if args.create_auth == True and args.client_id_file is not None:
        if args.client_id_file == "":
            print("error: argument 'clientid'; expected non empty argument")
            sys.exit(1)
        elif os.path.exists(args.client_id_file) == False:
            print("error: no such file; {}".format(args.client_id_file))
            sys.exit(1)
        else:
            client_id_file = os.path.abspath(args.client_id_file)

    # If token_file argument is given, file must exist if argument 'auth' is not specified (so, not an authentication action).
    if args.token_file is not None:
        if args.token_file == "":
            print("error: argument 'token_file'; expected non empty argument")
            sys.exit(1)
        else:
            token_file = os.path.abspath(args.token_file)

    if args.create_auth == False and os.path.exists(token_file) == False:
        print("error: no such file; {}".format(token_file))
        sys.exit(1)

    if args.run_upload == True:
        if args.album_name is None:
            print("error: argument 'album'; expected for upload")
            sys.exit(1)
        elif args.album_name == "":
            print("error: argument 'album'; expected non empty argument for upload")
            sys.exit(1)
        elif len(args.photos) == 0:
            print("error: argument 'photos'; expected for upload")
            sys.exit(1)
        elif args.photos[0] == "":
            print("error: argument 'photos'; expected non empty argument for upload")
            sys.exit(1)
        elif os.path.exists(args.photos[0]) == False:
            print("error: no such file; {}".format(args.photos[0]))
            sys.exit(1)

    #
    # End of validation.
    #

    session = get_authorized_session(client_id_file, token_file)

    # If action to create authentication token was requested, than it is the only thing to do (and it is done every time anyway), so exit.
    if args.create_auth == True:
        if session is not None:
            print("Auth token exists and seems valid.")
        return

    if args.run_upload == True:
        if upload_photos(session, args.photos, args.album_name) == False:
            sys.exit(1)
        return

    if args.albums_list == True:
        if args.album_name is None:
            printAlbums(session)
        elif args.album_name == "":
            print("error: argument 'album'; expected non empty argument")
            sys.exit(1)
        else:
            if printAlbumContent(session,args.album_name) == False:
                sys.exit(1)
        return
   
if __name__ == '__main__':
  main()
