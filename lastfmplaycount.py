# Original author: Bram Bonne
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# The Rhythmbox authors hereby grant permission for non-GPL compatible
# GStreamer plugins to be used and distributed together with GStreamer
# and Rhythmbox. This permission is above and beyond the permissions granted
# by the GPL license by which Rhythmbox is covered. If you modify this code
# you may extend this exception to your version of the code, but you are not
# obligated to do so. If you do not wish to do so, delete this exception
# statement from your version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.

import rb

import gi
from gi.repository import GObject, Gtk, Gdk, GdkPixbuf, Gio, Peas, RB

from xml.dom import minidom
from urllib import urlopen, urlencode

from threading import Thread

from ConfigParser import RawConfigParser
from os import path

LASTFM_API_KEY = "c1c872970090c90f65aed19c97519962"

class LastfmPlaycountPlugin (GObject.GObject, Peas.Activatable):
    __gtype_name__ = 'LastFmPlaycount'
    object = GObject.property(type=GObject.GObject)
	
    def __init__ (self):
        GObject.GObject.__init__ (self)

    def do_activate (self):
        """
        Called when plugin is activated
        """
        self.emitting_uri_notify = False
        self.db = self.object.props.db

        self._username = self.get_username()

        sp = self.object.props.shell_player
        self.player_cb_ids = (
	        sp.connect ('playing-song-changed', self.playing_entry_changed),
        )
        self.playing_entry_changed (sp, sp.get_playing_entry ())

    def do_deactivate (self):
        """
        Called when plugin is deactivated (or when rhythmbox exits)
        """
        sp = self.object.props.shell_player
        for id in self.player_cb_ids:
            sp.disconnect (id)
        self.player_cb_ids = ()
	
    def get_username(self):
        """
        Get the username from the session file of rhythmbox' audioscrobbler
        plugin as per http://mail.gnome.org/archives/rhythmbox-devel/2011-December/msg00029.html
        """
        config = RawConfigParser()
        # Expanduser expands '~' into '/home/<username>/'
        as_session = open(path.expanduser('~/.local/share/rhythmbox/audioscrobbler/sessions'), 'r')
        config.readfp(as_session)
        username = config.get('Last.fm', 'username')
        print "Parsed Last.fm username: %s" % username
        return username
	
    def playing_entry_changed (self, sp, entry):
        """
        Callback function. Called whenever another song starts playing
        @sp     Rhythmbox' shell
        @entry  The currently playing song
        """
        if entry is not None:
            # Start a new thread so UI is not blocked
            newthread = Thread(target=self.update_playcount, args=(entry,))
            newthread.start()

    def update_playcount (self, entry):
        """
        Updates The database entry for the song provided
        @entry  The song that needs to be updated
        """
        artist = entry.get_string(RB.RhythmDBPropType.ARTIST)
        title = entry.get_string(RB.RhythmDBPropType.TITLE)
        #old_playcount = entry.get_int(RB.RhythmDBPropType.PLAY_COUNT)
        playcount = self.get_playcount(artist, title)
        print "Setting playcount for \"%s - %s\" to %d" % (artist, title, playcount)
        self.db.entry_set(entry, RB.RhythmDBPropType.PLAY_COUNT, playcount)
        self.db.commit()
	
    def get_playcount(self, artist, title):
        """
        Invokes Last.fm's API to get the playcount for the provided song
        @artist The artist of the song
        @title  The title of the song
        """
        params = urlencode({'method':'track.getinfo', 'api_key':LASTFM_API_KEY,
            'artist':artist, 'track':title, 'username':self._username, 'autocorrect':1})
        response = minidom.parse(urlopen("http://ws.audioscrobbler.com/2.0/?%s" % params))
        playcount = response.getElementsByTagName("userplaycount")[0].childNodes[0].data
        playcount = int(playcount)
        return playcount
