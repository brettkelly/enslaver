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

import ConfigParser
import imp
import inspect
import logging
import os
import os.path
import sys
from logging.handlers import RotatingFileHandler
from optparse import OptionParser

# Evernote
import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.notestore.ttypes as NoteStoreTypes
import evernote.edam.type.ttypes as Types
from evernote.api.client import EvernoteClient


from enslaver.EnslaverPlugin import EnslaverPluginBase
from enslaver.EnslaverWriter import EvernoteWriter

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
    logDefault = 'DEBUG'
    parser = OptionParser(usage=usage)
    parser.add_option("-c", "--config", dest="config_path",
                      help="Use a different config file than the default",
                      default=".enslaver")
    parser.add_option("-l", "--loglevel", dest="loglevel", default=logDefault,
                      help="Log level = defaults to '%s'" % logDefault)
    parser.add_option("-q", "--quiet", dest="quiet",
                      help="Suppress normal output", action="store_true")
    parser.add_option("-t", "--test", dest="testMode",
                      help="Test mode; don't publish any output",
                      action="store_true")
    return parser

def slugToPluginName(slug):
    "Convert config slug to plugin file name"
    return "%sPlugin.py" % slug.capitalize()

def pluginNameToSlug(plugin):
    "Convert plugin name to config slug"
    return plugin.lower().replace('plugin','')


##
# Initialize options parser and logger
##
parser = getOptParser()
(options, args) = parser.parse_args()
loglevel = getattr(logging, options.loglevel.upper())
logger = getLogger(loglevel)
logger.info('#############################')
logger.info('##### ENSLAVER ACTIVATE #####')
logger.info('#############################')
logger.info('Options: %s' % options)

if options.config_path.startswith('~'):
    options.config_path = os.path.expanduser(options.config_path)

if not os.path.exists(options.config_path):
    print "Config file is missing; rerun the configuration script."
    raise SystemExit

##
# Load config
##

nonPluginConfigs = ['evernote','general']
cfdict = {}
plugins = []

config = ConfigParser.SafeConfigParser()
try:
    config.readfp(open(options.config_path))
except ConfigParser.Error, e:
    logger.critical("Error parsing config file:")
    logger.critical(e)
    logger.info("#### Quitting ####")

##
# Init Evernote
##
enconfig = {}

if not config.has_section('evernote'):
    logger.critical("Evernote config is missing")
    logger.info("#### Quitting ####")
    raise SystemExit

tokenFile = config.get('evernote', 'token')
if not os.path.exists(tokenFile):
    logger.critical("Evernote auth token file is missing")
    logger.info("#### Quitting ####")
    raise SystemExit

try:
    auth_token = open(tokenFile).read().strip()
    logger.debug('Auth token:')
    logger.debug(auth_token)
except IOError, e:
    logger.critical("Unable to read Evernote auth token file")
    logger.info("#### Quitting ####")
    raise SystemExit

enconfig['token'] = auth_token

if config.has_option('everote', 'sandbox'):
    useSandbox = bool(config.get('evernote', 'sandbox'))
else:
    useSandbox = True # sandbox is the default
enconfig['sandbox'] = useSandbox

if config.has_option('evernote', 'tags'):
    enconfig['tags'] = config.get('evernote','tags').split(',')

if config.has_option('evernote', 'notebook'):
    enconfig['notebook'] = config.get('evernote', 'notebook')

try:
    logger.debug("About to init EvernoteClient")
    logger.debug('Sandbox: '+ str(useSandbox))
    enclient = EvernoteClient(token=auth_token, sandbox=useSandbox)
    logger.debug("Init'd EvernoteClient")
    note_store = enclient.get_note_store()
    logger.debug("NoteStore instance created")
except Exception, e:
    logger.critical("Error initializing EvernoteClient:")
    logger.critical(e)
    raise SystemExit

try:
    enWriter = EvernoteWriter(enconfig, enclient, logger)
except Exception, e:
    logger.critical("Error initializing EvernoteWriter:")
    logger.critical(e)
    raise SystemExit

##
# Parse plugin config and load plugins
##

for configSection in config.sections():
    if configSection in nonPluginConfigs:
        continue
    cfdict[configSection] = {}
    for item in config.items(configSection):
        cfdict[configSection][item[0]] = config.get(configSection, item[0])

    pluginFile = slugToPluginName(configSection)
    pluginName = pluginFile[:-3]
    try:
        modInfo = imp.find_module(pluginName, ['plugins'])
        module = imp.load_module(pluginName, *modInfo)
    except ImportError, e:
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

##
# Run plugins and capture output
##
for p in plugins:
    logger.info('Running plugin: %s' % p._pluginName)
    feedData[p._pluginName] = {}
    pOutput = p.run()
    if type(pOutput) is not 'list':
        pOutput = [pOutput]
    feedData[p._pluginName]['data'] = pOutput # a list of EnslaverData objects
    # I Am Not A Computer Scientist
    feedData[p._pluginName]['config'] = cfdict[pluginNameToSlug(p._pluginName)]

if not feedData:
    logger.info('No data was returned by plugins.')
    logger.info('This could mean something bad happened, I dunno.')
    raise SystemExit

try:
    enWriter.write(feedData)
except Exception, e:
    logger.critical("Error writing to Evernote:")
    logger.critical(type(e))
    logger.critical(e)
    raise SystemExit

# Make sure the output is well-ish formed
#if options.testMode:
    #with open('output.html', 'w') as out:
        #for i in feedData.keys():
            #for j in feedData[i]:
                #for k in j:
                    #out.write(k.enmlContent)
