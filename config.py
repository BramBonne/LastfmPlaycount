from ConfigParser import RawConfigParser, NoSectionError
from os import path

CONFIGFILENAME = '~/.local/share/rhythmbox/audioscrobbler/lastfmplaycount'

class Config:
    """
    Read and write configuration data for Last.fm playcount sync plugin
    """
    
    def __init__(self):
        self._parse_username()
        
        self._config_parser = RawConfigParser()
        self._init_config()
        
    def __del__(self):
        self.write()
        
    def _init_config(self):
        """
        Reads the config file, and writes default values if the file doesn't exist yet
        """
        # Expanduser expands '~' into '/home/<username>/'
        try:
            configfile = open(path.expanduser(CONFIGFILENAME), 'r')
            self._config_parser.readfp(configfile)
        except:
            print "Config file does not exist. Using default values."
        # If no values exist, fill in default ones
        if not self._config_parser.has_option('LastFmPlaycount', 'update_playcounts'):
            self.set_update_playcounts(True)
        if not self._config_parser.has_option('LastFmPlaycount', 'update_ratings'):
            self.set_update_ratings(True)
        
    def get_username(self):
        """
        @return the user's Last.fm username
        """
        if self._username is None:
            # If the username was not filled in before, check if it is now
            self._username = self._retrieve_username()
            
        return self._username
        
    def get_update_playcounts(self):
        """
        @return Whether the user has specified that he wants his playcounts updated
        """
        return self._config_parser.getboolean('LastFmPlaycount', 'update_playcounts')
        
    def set_update_playcounts(self, update):
        """
        Sets whether the user wants his playcounts to be updated
        @update True if the user wants his playcounts to be updated
        """
        # Configparser only allows strings to be stored
        if update == True:
            update = 'True'
        else:
            update = 'False'
        try:
            self._config_parser.set('LastFmPlaycount', 'update_playcounts', update)
        except NoSectionError:
            self._config_parser.add_section('LastFmPlaycount')
            self._config_parser.set('LastFmPlaycount', 'update_playcounts', update)
        
    def get_update_ratings(self):
        """
        @return Whether the user has specified that he wants his ratings updated
        """
        return self._config_parser.getboolean('LastFmPlaycount', 'update_ratings')
        
    def set_update_ratings(self, update):
        """
        Sets whether the user wants his ratings to be updated
        @update True if the user wants his ratings to be updated
        """
        # Configparser only allows strings to be stored
        if update == True:
            update = 'True'
        else:
            update = 'False'
        try:
            self._config_parser.set('LastFmPlaycount', 'update_ratings', update)
        except NoSectionError:
            self._config_parser.add_section('LastFmPlaycount')
            self._config_parser.set('LastFmPlaycount', 'update_ratings', update)
        
    def write(self):
        """
        Writes config file to permanent storage
        """
        configfile = open(path.expanduser(CONFIGFILENAME), 'w')
        self._config_parser.write(configfile)
        
    def _parse_username(self):
        """
        Get the username from the session file of rhythmbox' audioscrobbler
        plugin as per http://mail.gnome.org/archives/rhythmbox-devel/2011-December/msg00029.html
        """
        username_config_parser = RawConfigParser()
        # Expanduser expands '~' into '/home/<username>/'
        as_session = open(path.expanduser('~/.local/share/rhythmbox/audioscrobbler/sessions'), 'r')
        username_config_parser.readfp(as_session)
        username = username_config_parser.get('Last.fm', 'username')
        print "Parsed Last.fm username: %s" % username
        self._username = username
