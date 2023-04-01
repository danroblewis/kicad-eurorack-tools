#!/bin/bash
set -x

cat .kicadsym_filepath | while read fname; do
  cp "$fname" library/symbols/
done

cat .kicad_pluginpath | while read fpath; do
  ls "$fpath"/* | while read i; do
    cp "$i" plugin/
  done
done
