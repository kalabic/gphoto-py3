#!/usr/bin/env bash

if [ -z "$1" ]
then
  echo "error: Missing album name."
  exit 1
fi

if [ -z "$2" ]
then
  echo "error: Missing photo name."
  exit 1
fi

# Test retrieving error code from python script into bash script.
gphotopy --up --album "$1" "$2"

result=$?
if [ $result -ne 0 ]; then
  echo "error code test: $result"
  exit 1
fi

 echo "error code test: OK"
