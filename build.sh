#!/bin/bash -x
set -x

# get current version
current_version="$(cat VERSION)"

# increment build number
v=$[`echo $current_version | grep -oE "[0-9]+$"`+1]
new_v="`echo "$current_version" | sed "s~[0-9]*$~$v~"`"
version="$new_v"

sed -i "s~$current_version~$version~g" packaging/packages.json
echo "$version" > VERSION

#./copy_from_kicad.sh

# plugin directories must have:
# /plugins/
# /plugins/__init__.py
# /resources/icon.png
# /metadata.json

mkdir -p build/plugin/plugins
cd build/plugin
mkdir resources
cp ../../icon.png .
echo "{
    \"\$schema\": \"https://go.kicad.org/pcm/schemas/v1\",
    \"name\": \"KiCAD Eurorack tools\",
    \"description\": \"A Eurorack integration addon for KiCAD\",
    \"description_full\": \"helps build eurorack audio synthesizer modules\",
    \"identifier\": \"com.github.danroblew.kicad-eurorack-tools\",
    \"type\": \"plugin\",
    \"author\": {
        \"name\": \"Daniel Lewis\",
        \"contact\": {
            \"twitter\": \"@danroblew\"
        }
    },
    \"maintainer\": {
        \"name\": \"Daniel Lewis\",
        \"contact\": {
            \"twitter\": \"@danroblew\"
        }
    },
    \"license\": \"WTFPL\",
    \"resources\": {
        \"homepage\": \"https://github.com/danroblew/kicad-eurorack-tools\"
    },
    \"versions\": [{
        \"version\": \"$VERSION\",
        \"status\": \"testing\",
        \"kicad_version\": \"7.0\"
    }]
}" > manifest.json
cp -rf ../../plugin/* plugins/
zip kicad-eurorack-tools-v$version.zip -r *
mv kicad-eurorack-tools-v$version.zip ..
cd ..



# content libraries must have:
# /footprints/somethin.mod
# /3dmodels/somethin.stp
# /3dmodels/somethin.wrl
# /symbols/somethin.sym
# /resources/icon.png
# /metadatajson

mkdir -p library/
cd library
cp -rf ../../library/* .
echo "{
    \"\$schema\": \"https://go.kicad.org/pcm/schemas/v1\",
    \"name\": \"KiCAD Eurorack library\",
    \"description\": \"A  parts library of the canonical Eurorack parts\",
    \"description_full\": \"helps build eurorack audio synthesizer modules\",
    \"identifier\": \"com.github.danroblew.kicad-eurorack-library\",
    \"type\": \"library\",
    \"author\": {
        \"name\": \"Daniel Lewis\",
        \"contact\": {
            \"twitter\": \"@danroblew\"
        }
    },
    \"maintainer\": {
        \"name\": \"Daniel Lewis\",
        \"contact\": {
            \"twitter\": \"@danroblew\"
        }
    },
    \"license\": \"WTFPL\",
    \"resources\": {
        \"homepage\": \"https://github.com/danroblew/kicad-eurorack-tools\"
    },
    \"versions\": [{
        \"version\": \"$version\",
        \"status\": \"testing\",
        \"kicad_version\": \"7.0\"
    }]
}" > manifest.json
zip kicad-eurorack-library-v$version.zip -r *
mv kicad-eurorack-library-v$version.zip ..
cd ..

# simulation
cat ../library/simulation/*.lib ../library/simulation/*.mod > kicad-eurorack-simulation-$version.lib

rm -rf library/ plugin/

cd ..

#git add .
#git commit -m "new version: $version"
#git push origin master
