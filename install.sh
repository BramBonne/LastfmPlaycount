#!/bin/bash

# install schema
sudo cp ./org.gnome.rhythmbox.plugins.lastfmplaycount.gschema.xml /usr/share/glib-2.0/schemas/
sudo glib-compile-schemas /usr/share/glib-2.0/schemas/

# install plugin
mkdir -p ~/.local/share/rhythmbox/plugins/lastfmplaycount/
cp * ~/.local/share/rhythmbox/plugins/lastfmplaycount

#if [[ $EUID -eq 0 ]]; then
#    echo "Installing system-wide (running as root)"
#    mkdir -p /usr/lib/rhythmbox/plugins/lastfmplaycount
#    cp * /usr/lib/rhythmbox/plugins/lastfmplaycount
#else
#    echo "Installing for the current user only"
#    mkdir -p ~/.local/share/rhythmbox/plugins/lastfmplaycount
#    cp * ~/.local/share/rhythmbox/plugins/lastfmplaycount
#fi
