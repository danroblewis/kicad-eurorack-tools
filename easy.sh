#!/bin/bash

git pull origin master
./copy_from_kicad.sh
dos2unix library/*/*kicad_sym
dos2unix plugin/*py
git diff
echo -n "Looks good?"
read
./publish.sh
