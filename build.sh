#!/bin/bash
set -x

version="$(cat VERSION)"


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
        \"kicad_version\": \"6.0\"
    }]
}" > manifest.json
cp -rf ../../plugin/* plugins/
zip kicad-eurorack-tools-$version.zip -r *
mv kicad-eurorack-tools-$version.zip ..
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
        \"kicad_version\": \"6.0\"
    }]
}" > manifest.json
zip kicad-eurorack-library-$version.zip -r *
mv kicad-eurorack-library-$version.zip ..
cd ..

# simulation
cat ../library/simulation/*.lib ../library/simulation/*.mod > kicad-eurorack-simulation-$version.lib

rm -rf library/ plugin/
