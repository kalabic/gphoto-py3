# gphotopy, gphotopy.ps1
Bash and PowerShell wrappers for `gphoto.py`. Use them with the same command line arguments (see help: `gphotopy -h`).

## Installing and running
**WINDOWS:** Remember, you need to run PowerShell script `gphotopy.ps1` in these steps, not `gphotopy` or `gphoto.py`!
1. Make sure you have Python 3.10 installed on your system.
2. Go to folder where you downloaded files from repository, run `gphotopy --install`.
   - (it will create Python virtual environment and download dependencies)
3. Authorize with Google:
   - Update client id and secret inside `auth/client_id.json`.
   - Run once `gphotopy --auth`, that will open system browser and ask permission to give access to your Google Photos to this script.
4. Add script directory to your PATH environment variable and use `gphotopy` (not Python script `gphoto.py`).
5. Run 'gphotopy -h' for help.

## NOTE:
1. Although script is fairly simple, you need to be familiar with Google's Cloud platform to get your own client id and client secret to enable it to use Google's server APIs. More details here in [wiki](https://github.com/kalabic/gphotos-upload-py3/wiki#google-photos-api-prerequisites).
2. Authentication will open default system browser. Works best with Chrome/Chromium, issues have been found with Firefox.
3. Script can only upload to albums that it has created. It does not have permission to upload to albums user has created manually through Google Photos web page. Pay attention to "IS WRITABLE?" value when listing all albums using "--ls" option.

# gphoto.py
Simple but flexible script to upload photos to Google Photos.

## Usage 

```
usage: gphoto.py [-h] [--auth  auth_file] [--album album_name]
                 [--log log_file]
                 [photo [photo ...]]

Examples:
  Create auth token: gphoto.py --auth
     Upload a photo: gphoto.py --up --album myalbum myphoto.jpeg
    List all albums: gphoto.py --ls
List items in album: gphoto.py --ls --album myalbum

positional arguments:
  photo               filename of a photo to upload

optional arguments:
  -h, --help            show this help message and exit
  --auth                Create authentication token if it does not exist, or
                        try to load it and exit.
  --clientid client_id_file
                        File where client id and secret is stored. Used in
                        combination with '--auth'. (optional, default is
                        'auth/client_id.json'
  --token token_file    File where authentication token is stored. (optional,
                        default is 'auth/token.json'
  --album album_name    Name of photo album to create (if it doesn't exist).
                        Any uploaded photos will be added to this album.
  --log log_file        Name of output file for log messages.
  --up                  Run upload to gphoto.
  --ls                  List all albums in gphoto. Combination with '--album'
                        will list all items in album.
```

## Setup

### Obtaining a Google Photos API key (Client ID and Client Secret)

1. Details here in [wiki](https://github.com/kalabic/gphotos-upload-py3/wiki#google-photos-api-prerequisites) and official page: [Getting started with Google Photos REST APIs](https://developers.google.com/photos/library/guides/get-started).
2. Replace `YOUR_CLIENT_ID` in the auth/client_id.json file with the provided Client ID.
3. Replace `YOUR_CLIENT_SECRET` in the auth/client_id.json file wiht the provided Client Secret.

### Installing dependencies and running the script - simple way, without Python virtual environment

1. Make sure you have [Python 3.10](https://www.python.org/downloads/) installed on your system
2. Change to the directory where you installed this script
3. Run:
   - `pip install -r requirements.txt` - download dependencies
4. Authorize with Google:
   - Update client id and secret inside `auth/client_id.json`.
   - Run once `python gphoto.py --auth`, that will open system browser and ask permission to give access to your Google Photos to this script.
5. Now run the script via `python gphoto.py` as desired. Use `python gphoto.py -h` to get help. 'auth' argument is not needed any more if previous step was successful.

### Installing dependencies and running the script - using Python virtual environment

1. Make sure you have [Python 3.10](https://www.python.org/downloads/) installed on your system
2. Change to the directory where you installed this script
3. Run:
   - `python3.10 -m venv venv` - to create Python virtual environment and download dependencies
   - `source venv/bin/activate` - enter Python venv shell
   - `pip install -r requirements.txt` - download dependencies
   - `deactivate` - exit Python shell
4. Authorize with Google:
   - Update client id and secret inside `auth/client_id.json`.
   - (activate venv when using script)
   - Run once `python gphoto.py --auth`, that will open system browser and ask permission to give access to your Google Photos to this script.
5. Again, always first activate Python venv when using script if you decided to install it this way (`source venv/bin/activate`).
6. Now run the script via `python gphoto.py` as desired. Use `python gphoto.py -h` to get help. 'auth' argument is not needed any more if previous step was successful.

For example, upload an image to album: `python gphoto.py --up --album TestAlbum TestImage.jpeg`
Or, list all albums: `python gphoto.py --ls`
