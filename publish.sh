#!/bin/bash -x
set -x

# get current version
current_version="$(cat VERSION)"

# increment build number
v=$[`echo $current_version | grep -oE "[0-9]+$"`+1]
version="`echo "$current_version" | sed "s~[0-9]*$~$v~"`"
echo "$version" > VERSION

sed "s~___VERSION___~$version~g" packaging/packages.json.tpl > packaging/packages.json

./copy_from_kicad.sh
git add .
git commit -m "new version"
git tag -a v$version -m v$version
git push origin master
git push origin master --tags
