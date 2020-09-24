#!/bin/bash
set -Eeuo pipefail

MY_DIR="$(readlink -f "$(dirname "$0")")"

dso --patch-string-table "$MY_DIR/playGui.gui.dso.json" scriptsAndAssets/client/ui/playGui.gui.dso
dso --patch-string-table "$MY_DIR/defaultGameProfiles.cs.dso.json" scriptsAndAssets/client/ui/defaultGameProfiles.cs.dso

find scriptsAndAssets/client/ui/special/images -name 'moto*.dds' -exec convert {} -filter cubic -resize 200% {} \;
find scriptsAndAssets/client/ui/special/images -name '*AtMinimap.dds' -exec convert {} -filter cubic -resize 200% {} \;
find scriptsAndAssets/client/ui/special/maps -name '*.png' -exec convert {} -filter cubic -resize 200% {} \;

sed -i -e 's/sizeX = "1024"/sizeX = "2048"/' -e 's/sizeY = "1024"/sizeY = "2048"/' \
       -e 's/sizeX = "512"/sizeX = "1024"/' -e 's/sizeY = "512"/sizeY = "1024"/' \
       -e 's/sizeX = "768"/sizeX = "1536"/' -e 's/sizeY = "768"/sizeY = "1536"/' \
       -e 's/Margin = "50"/Margin = "100"/' -e 's/Margin = "128"/Margin = "256"/' \
       scriptsAndAssets/data/missions/*.mis
