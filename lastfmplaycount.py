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
from urllib import urlopen

LASTFM_API_KEY = "c1c872970090c90f65aed19c97519962"
LASTFM_API_SECRET = "66ee536eddd3fb72a84b5780a54ef822"
LASTFM_USERNAME = "megooz" # TODO: make editable from interface

class LastfmPlaycountPlugin (GObject.GObject, Peas.Activatable):
	__gtype_name__ = 'LastFmPlaycount'
	object = GObject.property(type=GObject.GObject)

	def __init__ (self):
		GObject.GObject.__init__ (self)

	def do_activate (self):
		self.shell = self.object
		sp = self.shell.props.shell_player
		self.player_cb_ids = (
			sp.connect ('playing-song-changed', self.playing_entry_changed),
		)
		self.emitting_uri_notify = False
		self.db = self.shell.props.db
		self.current_entry = None
		self.playing_entry_changed (sp, sp.get_playing_entry ())

	def do_deactivate (self):
		sp = self.shell.props.shell_player
		for id in self.player_cb_ids:
			sp.disconnect (id)
		self.player_cb_ids = ()
		
	def playing_entry_changed (self, sp, entry):
		self.update_playcount(entry)

	def update_playcount (self, entry):
		artist = entry.get_string(RB.RhythmDBPropType.ARTIST)
		title = entry.get_string(RB.RhythmDBPropType.TITLE)
		#old_playcount = entry.get_int(RB.RhythmDBPropType.PLAY_COUNT)
		playcount = self.get_playcount(artist, title)
		print "Setting playcount for \"%s - %s\" to %d" % (artist, title, playcount)
		self.db.entry_set(entry, RB.RhythmDBPropType.PLAY_COUNT, playcount)
		self.db.commit()
		
	def get_playcount(self, artist, title):
		requesturi = "http://ws.audioscrobbler.com/2.0/?method=track.getinfo&api_key=%s&artist=%s&track=%s&username=%s&autocorrect=1" % (LASTFM_API_KEY, artist, title, LASTFM_USERNAME)
		response = minidom.parse(urlopen(requesturi))
		playcount = response.getElementsByTagName("userplaycount")[0].childNodes[0].data
		playcount = int(playcount)
		return playcount
