from ConfigParser import RawConfigParser
from os import path

class Config:
    """
    Read and write configuration data for Last.fm playcount sync plugin
    """
    
    def __init__(self):
        self._parse_username()
        
    def get_username(self):
        """
        @return the user's Last.fm username
        """
        if self._username is None:
            # If the username was not filled in before, check if it is now
            self._username = self._retrieve_username()
            
        return self._username
        
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
