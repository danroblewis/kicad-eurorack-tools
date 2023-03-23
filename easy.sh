#!/bin/bash

git pull origin master
./copy_from_kicad.sh
git diff
echo -n "Looks good?"
read
./publish.sh
