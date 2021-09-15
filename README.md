# gphotoup
# gphotos-upload fork
Simple but flexible script to upload photos to Google Photos. Useful if you have photos in a directory structure that you want to reflect as Google Photos albums.
The folders under the given root will become the albums in Google Photos. All the photos and videos found in these folders will be uploaded to albums.
If file with the same name is already part of album it will be skipped.

## Build
### build docker image
```
docker build -t gphotoup .
```
## Setup
### Obtaining a Google Photos API key

1. Obtain a Google Photos API key (Client ID and Client Secret) by following the instructions on [Getting started with Google Photos REST APIs](https://developers.google.com/photos/library/guides/get-started)
2. Replace `YOUR_CLIENT_ID` in the client_id.json file with the provided Client ID. 
3. Replace `YOUR_CLIENT_SECRET` in the client_id.json file wiht the provided Client Secret.

### First run
On first run you'll be asked for auth token.
Copy the URL from shell, open the browser window and go through procedure.
Copy the token form web an paste it to shell.
The token will be saved in auth/auth.txt file.
Use volume in docker mode for ./auth folder to save your authentication.
## Usage (docker mode)
```
# upload all from /photo_folder
docker run -it --rm --name gphotoup -v /tmp/auth:/app/auth -v /tmp/pht:/photo_folder gphotoup
# run shell in container 
docker run -it --rm --name gphotoup -v /tmp/auth:/app/auth -v /tmp/pht:/photo_folder gphotoup /bin/bash
```

### Installing dependencies and running the script

1. Make sure you have [Python 3.7](https://www.python.org/downloads/) installed on your system
2. Run `pipenv shell` to open a shell with all the dependencies available (you'll need to do this every time you want to run the script)
3. Now run the script via `python upload.py` as desired. Use `python upload.py -h` to get help.

## Usage (script) 

```
usage: upload.py [-h] [--auth  auth_file] [--path  root_folder]
                 [--album album_name] [--log log_file] [--up] [--ls]
                 [photo [photo ...]]
Upload photos to Google Photos.
positional arguments:
  photo                filename of a photo to upload
optional arguments:
  -h, --help           show this help message and exit
  --auth  auth_file    file for reading/storing user authentication tokens (default='auth/auth.txt')
  --path  root_folder  path to root of album album folders
  --album album_name   name of photo album to create (if it doesn't exist).
                       Any uploaded photos will be added to this album.
  --log log_file       name of output file for log messages
  --up                 run upload to gphoto  (default='.')
  --ls                 list all albums in gphoto
```