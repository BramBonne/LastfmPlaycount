# Info

The Last.fm playcount synchronization plugin for Rhythmbox fetches the
currently playing track's playcount from Last.fm, and updates your Rhythmbox
database accordingly.
The Last.fm username is read from Rhythmbox' Last.fm plugin.


# Installing

To install the plugin for the current user only, run the install script with
```
./install.sh
```

To install system-wide (for all users), run this script as root with
```
sudo ./install.sh
```

# How to enable

After installing the plugin in one of the two ways mentioned above, start up Rhythmbox, and head over to the "Edit > Plugins" menu. Check the box next to "Last.fm playcount synchronization".
Also make sure that you also have the regular "Last.fm" plugin enabled, since your Last.fm credentials stored in this plugin are used by the Last.fm playcount synchronization plugin to get the correct playcounts.


# Credits

Plugin created by Bram Bonné <bram.bonne at gmail dot com>
Bug reports and suggestions welcome at [Github](https://github.com/BramBonne/LastfmPlaycount/issues)
