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
import urllib

from threading import Thread
from time import sleep

from lastfmplaycountconfig import Config

LASTFM_API_KEY = "c1c872970090c90f65aed19c97519962"

class LastfmPlaycountPlugin (GObject.GObject, Peas.Activatable):
    object = GObject.property(type=GObject.GObject)

    def __init__ (self):
        GObject.GObject.__init__ (self)

    def do_activate (self):
        """
        Called when plugin is activated
        """
        self._update_all_thread = None
        self.shell = self.object
        self.db = self.shell.props.db
        self.app = self.shell.props.application

        self._config = Config()

        sp = self.shell.props.shell_player
        self.player_cb_ids = (
            sp.connect ('playing-song-changed', self.playing_entry_changed),
        )
        self.playing_entry_changed (sp, sp.get_playing_entry ())

        self._init_ui()

        self.running = True
        print("Activation finished")

    def do_deactivate (self):
        """
        Called when plugin is deactivated (or when rhythmbox exits)
        """
        self.running = False

        if self._update_all_thread is not None and self._update_all_thread.is_alive:
            print("Stopping update of playcounts")
            self._update_all_thread.join(1)

        sp = self.shell.props.shell_player
        for id in self.player_cb_ids:
            sp.disconnect (id)
        self.player_cb_ids = ()

        self._config.write()

        # Delete all references. This is needed according to the reference doc
        # at https://wiki.gnome.org/Apps/Rhythmbox/Plugins/WritingGuide
        del self.shell
        del self.db
        del self.app
        del self.update_menu_item
        del self.update_action
        del self._update_all_thread
        del self.running

    def _init_ui (self):
        # Used https://github.com/fossfreedom/alternative-toolbar/blob/master/alttoolbar_rb3compat.py as documentation
        print("Extending the UI with our own actions")
        self.update_action = Gio.SimpleAction(name="updatelastfmplaycount")
        self.update_action.connect('activate', self.update_all)
        self.app.add_action(self.update_action)

        self.update_menu_item = Gio.MenuItem()
        # So, if you're reading this code hoping to find the solution to all
        # your gobject woes, then please do note the "app." prefix on the next
        # line. It will make your life okay again, I promise.
        self.update_menu_item.set_detailed_action('app.updatelastfmplaycount')
        self.update_menu_item.set_label("Update Last.fm playcount")
        self.app.add_plugin_menu_item('tools', 'updatelastfmplaycount', self.update_menu_item)

    def update_all (self, args, kwargs):
        """
        Update the entire library in a separate thread.
        Calling this function might take a while, as the last.fm service restricts
        the maximum number of API calls per minute
        @args given to us by Gio, ignored
        @kwargs given to us by Gio, ignored
        """
        if self._update_all_thread is not None and self._update_all_thread.is_alive:
            print("Not starting a new update_all thread because a previous\
                    one is already running")
            return
        self._update_all_thread = Thread(target=self._update_all_unthreaded, args=())
        self._update_all_thread.start()

    def _update_all_unthreaded (self):
        """
        Update the entire library.
        Calling this function might take a while, as the last.fm service restricts
        the maximum number of API calls per minute
        This is a helper function to update_all
        """
        print("Starting update of entire collection")
        try:
            self.db.entry_foreach_by_type(self.db.entry_type_get_by_name("song"), self._update_entry_slowly)
        except InterruptedError:
            print("Updating of all playcounts was interrupted")

    def _update_entry_slowly(self, entry):
        """
        Helper function for _update_all_unthreaded, to allow us to adhere to
        Last.fm's API call limits by sleeping for 1 second between every call.
        @entry  The song that needs to be updated
        """
        self.update_entry(entry)
        sleep(1)

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

    def update_entry (self, entry):
        """
        Updates The database entry for the song provided
        @entry  The song that needs to be updated
        """
        if entry is None:
            return
        if not self.running:
            # Rhythmbox is exiting. Stop updating new entries
            raise InterruptedError()
        artist = entry.get_string(RB.RhythmDBPropType.ARTIST)
        title = entry.get_string(RB.RhythmDBPropType.TITLE)
        try:
            playcount, lovedtrack = self.get_lastfm_info(artist, title)
            if self._config.get_update_playcounts():
                old_playcount = entry.get_ulong(RB.RhythmDBPropType.PLAY_COUNT)
                print("Setting playcount of \"%r - %r\" to %d" % (artist, title, playcount))
                if old_playcount < playcount:
                    self.db.entry_set(entry, RB.RhythmDBPropType.PLAY_COUNT, playcount)
                elif old_playcount > playcount:
                    print("Old playcount for \"%r - %r\" was higher than the new one (%d instead of %d). Not updating (assuming last.fm knows less)" % (artist, title, old_playcount, playcount))
                else:
                    print("Playcount for \%r - \%r remained the same. Not updating" % (artist, title))
            if self._config.get_update_ratings() and lovedtrack:
                print("Setting rating of \"%r - %r\" to 5 (loved track)" % (artist, title))
                self.db.entry_set(entry, RB.RhythmDBPropType.RATING, 5)
            self.db.commit()
        except IOError as e:
            print("Could not update \"%r - %r\ (error (%r): %s)" % (artist, title, e.errno, e.strerror))

    def get_lastfm_info(self, artist, title):
        """
        Invokes Last.fm's API to get the playcount for the provided song
        @artist The artist of the song
        @title  The title of the song
        @return The playcount, and whether or not the track is loved
        """
        params = urllib.parse.urlencode({'method':'track.getinfo', 'api_key':LASTFM_API_KEY,
            'artist':artist, 'track':title, 'username':self._config.get_username(), 'autocorrect':1})
        response = minidom.parse(urllib.request.urlopen("http://ws.audioscrobbler.com/2.0/?%s" % params))
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
