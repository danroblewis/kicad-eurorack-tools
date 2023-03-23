#!/bin/bash -x
set -x

# increment build number
v=$[`echo $current_version | grep -oE "[0-9]+$"`+1]
version="`echo "$current_version" | sed "s~[0-9]*$~$v~"`"

./copy_from_kicad.sh
git add .
git commit -m "new version"
git tag -a v$version -m v$version
git push origin master
git push origin master --tags
