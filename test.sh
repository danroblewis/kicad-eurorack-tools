#!/bin/bash -x
set -x


# increment build number
current_version="$(cat VERSION)"
v=$[`echo $current_version | grep -oE "[0-9]+$"`+1]
new_v="`echo "$current_version" | sed "s~[0-9]*$~$v~"`"
version="$new_v"
echo $version > VERSION

./copy_from_kicad.sh
git add .
git commit -m "test release"
git tag -a v$version -m v$version
git push origin master --tags
