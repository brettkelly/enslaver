#!/usr/bin/env python

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

"""
Main executable

- Init logger
- Init CLI args

1. verify config is present
    if not, prompt the user to rerun the config script
2. verify Evernote auth token is present
    if not, rerun the OAuth process
3. verify no pending notes are waiting to be created
    if so, stick them into Evernote
4. load all plugins in /plugins directory
5. match config section with plugin filename
6. execute plugins, write results to temporary file
7. connect to evernote and attempt to create notes
8. if notes can't be created, save the output file for next time
    save date/time of creation so it can be correctly set 
"""

##
# Stop-gap
##

import logging
import imp
import os
import os.path
import sys
from logging.handlers import RotatingFileHandler
from optparse import OptionParser
import ConfigParser
import inspect

from enslaver.EnslaverPlugin import EnslaverPluginBase
#from plugins import *


def getLogger(level=logging.ERROR):
    """Create, configure and return a Logger instance"""
    # Rotation settings
    fname = 'logs/enslaver.log'
    mode = 'a' # append
    mbytes = 1024 * 500 # 500kb per log file
    bkupCnt = 10 # number of backup files to keep around after rotation

    rfHandler = RotatingFileHandler(fname,mode,mbytes,bkupCnt)

    # Log format
    FMT = '%(asctime)s \t %(levelname)s \t %(message)s'
    rfHandler.setFormatter(logging.Formatter(FMT))

    # logger object
    logger = logging.getLogger('enslaver')
    logger.addHandler(rfHandler)
    logger.setLevel(level)
    n = logging.getLevelName(level)
    logger.debug('Logger initialized to level %s' % n)
    return logger

def getOptParser(usage=None):
    """Create, configure and return an OptionParser instance"""

    parser = OptionParser(usage=usage)
    parser.add_option("-c", "--config", dest="config_path",
                      help="Use a different config file than the default",
                      default="~/.enslaver")
    parser.add_option("-l", "--loglevel", dest="loglevel", default='ERROR',
                      help="Log level = defaults to 'ERROR'")
    parser.add_option("-q", "--quiet", dest="quiet",
                      help="Suppress normal output", action="store_true")
    parser.add_option("-t", "--test", dest="testMode",
                      help="Test mode; don't publish any output",
                      action="store_true")
    return parser

def slugToPluginName(slug):
    "Convert config slug to plugin file name"
    return "%sPlugin.py" % slug.capitalize()


##
# Initialize options parser and logger
##
parser = getOptParser()
(options, args) = parser.parse_args()
loglevel = getattr(logging, options.loglevel.upper())
logger = getLogger(loglevel)
logger.info('Options: %s' % options)

if options.config_path.startswith('~'):
    options.config_path = os.path.expanduser(options.config_path)

if not os.path.exists(options.config_path):
    print "Config file is missing; rerun the configuration script."
    raise SystemExit

##
# Parse plugin config and load plugins
##

cfdict = {}
plugins = []

config = ConfigParser.SafeConfigParser()
try:
    config.readfp(open(options.config_path))
except ConfigParser.Error, e:
    logger.critical("Error parsing config file:")
    logger.critical(e)
    logger.info("#### Quitting ####")

for configSection in config.sections():
    for item in config.items(configSection):
        cfdict[configSection] = {}
        cfdict[configSection][item[0]] = item[1]

    pluginFile = slugToPluginName(configSection)
    pluginName = pluginFile[:-3]
    modInfo = imp.find_module(pluginName, ['plugins'])
    try:
        module = imp.load_module(pluginName, *modInfo)
    except ImportError:
        logger.error("ImportError while loading %s:" % pluginName)
        logger.error(e)
        continue

    try:
        pInstance = getattr(module, pluginName)(cfdict[configSection], logger)
    except Exception, e:
        logger.error("Exception creating instance of %s" % pluginName)
        logger.error(type(e))
        logger.error(e)
        continue

    plugins.append(pInstance)

feedData = {}

for p in plugins:
    feedData[p._pluginName] = p.run()
print feedData

