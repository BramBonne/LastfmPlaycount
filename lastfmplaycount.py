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

from gi.repository import GObject, Peas, RB

from xml.dom import minidom
from urllib import urlopen, urlencode

from threading import Thread
from time import sleep

from lastfmplaycountconfig import Config

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
        self._updating_all = False
        self.emitting_uri_notify = False
        self.db = self.object.props.db

        self._config = Config()

        sp = self.object.props.shell_player
        self.player_cb_ids = (
	        sp.connect ('playing-song-changed', self.playing_entry_changed),
        )
        self.playing_entry_changed (sp, sp.get_playing_entry ())
        print "Activation finished"

    def do_deactivate (self):
        """
        Called when plugin is deactivated (or when rhythmbox exits)
        """
        sp = self.object.props.shell_player
        for id in self.player_cb_ids:
            sp.disconnect (id)
        self.player_cb_ids = ()
                
    def update_all(self):
        """
        Update the entire library in a separate thread.
        Calling this function might take a while, as the last.fm service restricts
        the maximum number of API calls per minute
        """
        newthread = Thread(target=self._update_all_unthreaded, args=())
        newthread.start()
    
    def _update_all_unthreaded (self):
        """
        Update the entire library.
        Calling this function might take a while, as the last.fm service restricts
        the maximum number of API calls per minute
        This is a helper function to update_all
        """
        if not self._updating_all:
            print "Starting update of entire collection"
            self._updating_all = True
            for id in range(self.db.entry_count()):
                self.update_entry(self.db.entry_lookup_by_id(id))
                sleep(1)
            self._updating_all = False
            self.set_run_update_all(False)

    def playing_entry_changed (self, sp, entry):
        """
        Callback function. Called whenever another song starts playing
        @sp     Rhythmbox' shell
        @entry  The currently playing song
        """
        if entry is not None:
            # Start a new thread so UI is not blocked
            newthread = Thread(target=self.update_entry, args=(entry,))
            newthread.start()
        #Ugly hack because I can't seem to be able to access the main class in the config class
        if self._config.get_run_update_all() and not self._updating_all:
            print "Calling update_all"
            self.update_all()

    def update_entry (self, entry):
        """
        Updates The database entry for the song provided
        @entry  The song that needs to be updated
        """
        if entry is None:
            return
        artist = entry.get_string(RB.RhythmDBPropType.ARTIST)
        title = entry.get_string(RB.RhythmDBPropType.TITLE)
        try:
            playcount, lovedtrack = self.get_lastfm_info(artist, title)
            if self._config.get_update_playcounts():
                old_playcount = entry.get_ulong(RB.RhythmDBPropType.PLAY_COUNT)
                if old_playcount < playcount:
                    print "Setting playcount of \"%r - %r\" to %d" % (artist, title, playcount)
                    self.db.entry_set(entry, RB.RhythmDBPropType.PLAY_COUNT, playcount)
                elif old_playcount > playcount:
                    print "Old playcount for \"%r - %r\" was higher than the new one (%d instead of %d). Not updating (assuming last.fm knows less)" % (artist, title, old_playcount, playcount)
                else:
                    print "Playcount for \%r - \%r remained the same. Not updating" % (artist, title)
            if self._config.get_update_ratings() and lovedtrack:
                print "Setting rating of \"%r - %r\" to 5 (loved track)" % (artist, title)
                self.db.entry_set(entry, RB.RhythmDBPropType.RATING, 5)
            self.db.commit()
        except IOError as (errno, strerror):
            print "Could not update \"%r - %r\ (error (%r): %s)" % (artist, title, errno, strerror)
        
    def get_lastfm_info(self, artist, title):
        """
        Invokes Last.fm's API to get the playcount for the provided song
        @artist The artist of the song
        @title  The title of the song
        @return The playcount, and whether or not the track is loved
        """
        params = urlencode({'method':'track.getinfo', 'api_key':LASTFM_API_KEY,
            'artist':artist, 'track':title, 'username':self._config.get_username(), 'autocorrect':1})
        response = minidom.parse(urlopen("http://ws.audioscrobbler.com/2.0/?%s" % params))
        try:
            playcount = response.getElementsByTagName("userplaycount")[0].childNodes[0].data
            playcount = int(playcount)
        except:
            playcount = 0
        try:
            lovedtrack = response.getElementsByTagName("userloved")[0].childNodes[0].data
            lovedtrack = bool(int(lovedtrack))
        except:
            lovedtrack = False
        return (playcount,lovedtrack)
