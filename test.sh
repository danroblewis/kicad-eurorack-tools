#!/bin/bash -x
set -x


inc=$(cat inc)
inc=$[$inc+1]
echo $inc > inc
version="v0.0.16_test$inc"

./copy_from_kicad.sh
git add .
git commit -m "test release"
git tag -a $version -m $version
git push origin master --tags
