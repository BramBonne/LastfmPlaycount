from configparser import RawConfigParser
from os import path

import rb

from gi.repository import GObject, Gtk, Gio, PeasGtk

DCONF_DIR = 'org.gnome.rhythmbox.plugins.lastfmplaycount'

class Config(GObject.GObject, PeasGtk.Configurable):
    """
    Read and write configuration data for Last.fm playcount sync plugin
    """
    __gtype_name__ = 'LastfmplaycountConfig'

    def __init__(self):
        self._parse_username()
        self.settings = Gio.Settings(DCONF_DIR)

    def do_create_configure_widget(self):
        """
        Called when the configuration UI button is pressed
        """
        print("Creating configuration dialog")
        builder = Gtk.Builder()
        builder.add_from_file(rb.find_plugin_file(self, "lastfmplaycount-prefs.ui"))

        dialog = builder.get_object('lastfmplaycountsync-preferences')
        if self.get_username() is not None:
            builder.get_object('username').set_markup('Detected username: ' + self.get_username())
        builder.get_object('update_playcounts').set_active(self.get_update_playcounts())
        builder.get_object('update_ratings').set_active(self.get_update_ratings())
        builder.get_object('loved_rating').set_range(0,5)
        builder.get_object('loved_rating').set_value(5)
        builder.get_object('rating_box').set_sensitive(False)

        callbacks = {
            "update_playcounts_toggled" : self._update_playcounts_toggled,
            "update_ratings_toggled" : self._update_ratings_toggled,
        }
        builder.connect_signals(callbacks)

        return dialog

    def get_username(self):
        """
        @return the user's Last.fm username
        """
        if not hasattr(self, '_username') or self._username is None:
            # If the username was not filled in before, check if it is now
            self._username = self._parse_username()

        return self._username

    def get_update_playcounts(self):
        """
        @return Whether the user has specified that he wants his playcounts updated
        """

        return self.settings["update-playcounts"]

    def set_update_playcounts(self, update):
        """
        Sets whether the user wants his playcounts to be updated
        @param update True if the user wants his playcounts to be updated
        """

        print("Setting updating of playcounts to %r" % update)
        self.settings["update-playcounts"] = update

    def get_update_ratings(self):
        """
        @return Whether the user has specified that he wants his ratings updated
        """
        return self.settings["update-ratings"]

    def set_update_ratings(self, update):
        """
        Sets whether the user wants his ratings to be updated
        @param update True if the user wants his ratings to be updated
        """
        print( "Setting updating of ratings to %r" % update)
        self.settings["update-ratings"] = update

    def _parse_username(self):
        """
        Get the username from the session file of rhythmbox' audioscrobbler
        plugin as per http://mail.gnome.org/archives/rhythmbox-devel/2011-December/msg00029.html
        """
        username_config_parser = RawConfigParser()
        # Expanduser expands '~' into '/home/<username>/'
        as_session = open(path.expanduser('~/.local/share/rhythmbox/audioscrobbler/sessions'), 'r')
        username_config_parser.readfp(as_session)
        try:
            username = username_config_parser.get('Last.fm', 'username')
            print("Parsed Last.fm username: %s" % username)
            self._username = username
        except:
            print("Error: last.fm sessions file could not be parsed. Username set to 'None'")
            self._username = None

    def _update_playcounts_toggled(self, widget):
        """
        Callback function
        @param widget The widget containing the toggle button
        """
        enabled = widget.get_active()
        print(enabled)
        self.set_update_playcounts(enabled)

    def _update_ratings_toggled(self, widget):
        """
        Callback function
        @param widget The widget containing the toggle button
        """
        enabled = widget.get_active()
        print(enabled)
        self.set_update_ratings(enabled)
