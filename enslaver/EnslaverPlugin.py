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

import feedparser
import inspect
import os
import time
import EnslaverData

class EnslaverPluginBase(object):
    "Base class for Enslaver plugins"

    def __init__(self, logger):
        self._pluginFile = inspect.getfile(inspect.currentframe())
        self._pluginName = self.__class__.__name__
        self.logger = logger

    def readFeedData(self, feed):
        output = {}
        try:
            data = feedparser.parse(feed)
            output['data'] = data
            output['read'] = time.time()
            return output
        except Exception, e:
            self.logger.error("==============")
            self.logger.error('Error parsing feed')
            self.logger.error(feed)
            self.logger.error(type(e))
            self.logger.error(e)
            self.logger.error("==============")
            return None
        self.logger.debug("Finished loading feed")
        self.logger.debug(feed)
