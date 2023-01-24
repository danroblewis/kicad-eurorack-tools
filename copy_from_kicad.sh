#!/bin/bash
set -x

cat .kicadsym_filepath | while read fname; do
  cp "$fname" library/symbols/
done
