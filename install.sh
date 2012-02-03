#!/bin/bash

if [[ $EUID -eq 0 ]]; then
    echo "Installing system-wide (running as root)"
    mkdir -p /usr/lib/rhythmbox/plugins/lastfmplaycount
    cp * /usr/lib/rhythmbox/plugins/lastfmplaycount
else
    echo "Installing for the current user only"
    mkdir -p ~/.local/share/rhythmbox/plugins/lastfmplaycount
    cp * ~/.local/share/rhythmbox/plugins/lastfmplaycount
fi
