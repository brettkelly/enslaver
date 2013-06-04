# Copyright (c) 2013, Brett Kelly

# Permission is hereby granted, free of charge, to any person obtaining a copy 
# of this software and associated documentation files (the "Software"), to deal 
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is furnished 
# to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in 
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS 
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS 
# IN THE SOFTWARE.

##
# Grab Last.fm user information and save it
##

import feedparser 

from enslaver.EnslaverPlugin import EnslaverPluginBase
from enslaver.EnslaverData import EnslaverData

class LastfmPlugin(EnslaverPluginBase):
    "Last.fm plugin for Enslaver"

    def __init__(self, config, logger):
        self.logger = logger
        self.logger.debug(config)
        self.user = config['username']
        self.recentFeed = \
            "http://ws.audioscrobbler.com/1.0/user/%s/recenttracks.rss?limit=100" % self.user
        self.lovedFeed = \
            "http://ws.audioscrobbler.com/1.0/user/%s/lovedtrackes.rss?limit=100" % self.user
        EnslaverPluginBase.__init__(self, logger)
    
    def run(self):
        self.logger.debug('%s.run() called' % self.__class__.__name__)
        recentData = None
        lovedData = None
        try:
            self.logger.debug('Retrieving recent tracks feed')
            recentData = feedparser.parse(self.recentFeed)
        except Exception, e:
            self.logger.error("Error reading Recent Tracks feed:")
            self.logger.error(type(e))
            self.logger.error(e)

        try:
            lovedData = feedparser.parse(self.lovedFeed)
        except Exception, e:
            self.logger.error("Error reading Loved Tracks feed:")
            self.logger.error(type(e))
            self.logger.error(e)

        recentOutput = ''
        if recentData:
            recentOutput = '<ul style="margin-bottom:5px">'
            for item in recentData.entries:
                url = item['links'][0]['href'].replace('&', '&amp;')
                name = item['title'].replace(u'\u2013', '--').replace('&', '&amp;')
                recentOutput += '<li><a href="%s">%s</a></li>' % (url, name)
            recentOutput += '</ul>'
        else:
            self.logger.debug('no recentData content')

        # Serious DRY violation follows.

        lovedOutput = ''
        if lovedData and lovedData.entries:
            lovedOutput = '<ul style="margin-bottom:5px">'
            for item in lovedData.entries:
                url = item['links'][0]['href'].replace('&', '&amp;')
                name = item['title'].replace(u'\u2013', '--').replace('&', '&amp;')
                lovedOutput += '<li><a href="%s">%s</a></li>' % (url, name)
            lovedOutput += '</ul>'
        else:
            self.logger.debug('no lovedData content')

        rData = EnslaverData("Today's Tracks", "Songs played according to Last.fm", recentOutput)
        lData = EnslaverData("Loved Today", "Songs loved on Last.fm today", lovedOutput)
    
         
        return [rData, lData]
