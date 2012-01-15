import gconf

from ConfigParser import RawConfigParser, NoSectionError
from os import path

GCONF_DIR = '/apps/rhythmbox/plugins/lastfmplaycount'

class Config:
    """
    Read and write configuration data for Last.fm playcount sync plugin
    """
    
    def __init__(self):
        self._parse_username()
        
        self._gconf_client = gconf.client_get_default()
        self._gconf_client.add_dir(GCONF_DIR, gconf.CLIENT_PRELOAD_RECURSIVE)
        
        self._init_config()
        
    def __del__(self):
        self.write()
        
    def _init_config(self):
        """
        Creates default values if none exist (this should actually be solved
        with a GConf Schema, but documentation seems to be available only behind
        the gates of Mordor).
        """
        if self._gconf_client.get_without_default(GCONF_DIR + '/update_playcounts') is None:
            self.set_update_playcounts(True)
        if self._gconf_client.get_without_default(GCONF_DIR + '/update_ratings') is None:
            self.set_update_ratings(True)
        
    def get_username(self):
        """
        @return the user's Last.fm username
        """
        if self._username is None:
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
        @update True if the user wants his playcounts to be updated
        """
        self._gconf_client.set_bool(GCONF_DIR + '/update_playcounts', update)
        
    def get_update_ratings(self):
        """
        @return Whether the user has specified that he wants his ratings updated
        """
        return self._gconf_client.get_bool(GCONF_DIR + '/update_ratings')
        
    def set_update_ratings(self, update):
        """
        Sets whether the user wants his ratings to be updated
        @update True if the user wants his ratings to be updated
        """
        self._gconf_client.set_bool(GCONF_DIR + '/update_ratings', update)
        
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
