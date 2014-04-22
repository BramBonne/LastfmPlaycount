try:
    from gi.repository import GConf
except ImportError:
    import gconf

from ConfigParser import RawConfigParser, NoSectionError
from os import path

import rb
import gi
from gi.repository import GObject, Gtk, Gdk, GdkPixbuf, Gio, PeasGtk, RB

GCONF_DIR = '/apps/rhythmbox/plugins/lastfmplaycount'

class Config(GObject.GObject, PeasGtk.Configurable):
    """
    Read and write configuration data for Last.fm playcount sync plugin
    """
    __gtype_name__ = 'LastfmplaycountConfig'
    
    def __init__(self):
        self._run_update_all = False #Ugly hack because I can't seem to be able to access the main class here
    
        self._parse_username()
        try:
            self._gconf_client = GConf.Client.get_default()
            self._gconf_client.add_dir(GCONF_DIR, GConf.ClientPreloadType.PRELOAD_RECURSIVE)
        except Exception as e:
            self._gconf_client = gconf.client_get_default()
            self._gconf_client.add_dir(GCONF_DIR, gconf.CLIENT_PRELOAD_RECURSIVE)
        
        self._init_config()
        
    def __del__(self):
        self.write()
        
    def _init_config(self):
        """
        Creates default values if none exist (this should actually be solved
        with a GConf Schema, but documentation seems to be locked tight behind
        the gates of Mordor).
        """
        if self._gconf_client.get_without_default(GCONF_DIR + '/update_playcounts') is None:
            self.set_update_playcounts(True)
        if self._gconf_client.get_without_default(GCONF_DIR + '/update_ratings') is None:
            self.set_update_ratings(True)
        self.set_run_update_all(False)
            
    def do_create_configure_widget(self):
        """
        Called when the configuration UI button is pressed
        """
        print "Creating configuration dialog"
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
            "sync_collection" : self._sync_collection,
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
        return self._gconf_client.get_bool(GCONF_DIR + '/update_playcounts')
        
    def set_update_playcounts(self, update):
        """
        Sets whether the user wants his playcounts to be updated
        @param update True if the user wants his playcounts to be updated
        """
        print "Setting updating of playcounts to %r" % update
        self._gconf_client.set_bool(GCONF_DIR + '/update_playcounts', update)
        
    def get_update_ratings(self):
        """
        @return Whether the user has specified that he wants his ratings updated
        """
        return self._gconf_client.get_bool(GCONF_DIR + '/update_ratings')
        
    def set_update_ratings(self, update):
        """
        Sets whether the user wants his ratings to be updated
        @param update True if the user wants his ratings to be updated
        """
        print "Setting updating of ratings to %r" % update
        self._gconf_client.set_bool(GCONF_DIR + '/update_ratings', update)
        
    def get_run_update_all(self):
        """
        @return Whether the collection is being updated right now
        """
        return self._gconf_client.get_bool(GCONF_DIR + '/run_update_all')
        
    def set_run_update_all(self, update):
        """
        Sets whether the collection should be updated right now
        @param update True if we should start updating the collection
        """
        print "Run_update %r" % update
        self._gconf_client.set_bool(GCONF_DIR + '/run_update_all', update)
        
    def write(self):
        """
        Writes config file to permanent storage
        """
        # Not needed for gconf
        pass
                
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
            print "Parsed Last.fm username: %s" % username
            self._username = username
        except:
            print "Error: last.fm sessions file could not be parsed. Username set to 'None'"
            self._username = None
            
    def _update_playcounts_toggled(self, widget):
        """
        Callback function
        @param widget The widget containing the toggle button
        """
        enabled = widget.get_active()
        print enabled
        self.set_update_playcounts(enabled)
        
    def _update_ratings_toggled(self, widget):
        """
        Callback function
        @param widget The widget containing the toggle button
        """
        enabled = widget.get_active()
        print enabled
        self.set_update_ratings(enabled)
        
    def _sync_collection(self, widget):
        """
        Callback function
        @param widget The button
        """
        self.set_run_update_all(True) #Ugly hack because I can't seem to be able to access the main class here
