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

import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.notestore.ttypes as NoteStoreTypes
import evernote.edam.type.ttypes as Types
import evernote.edam.error.ttypes as Errors
from datetime import date

class EvernoteWriter(object):
    "Writer for Evernote"
    def __init__(self, config, client, logger):
        self.config = config
        self.note_store = client.get_note_store()
        self.logger = logger
        self.logger.debug('Evernote config:')
        self.logger.debug(str(self.config))

    def _findOrCreateNotebook(self):
        useDefault = False
        try:
            notebook = self.config['notebook']
        except KeyError, e:
            self.logger.info("Notebook not defined in config; using default notebook")
            useDefault = True
        
        if useDefault:
            try:
                nb = self.note_store.getDefaultNotebook()
            except Errors.EDAMUserException, ue:
                self.logger.critical("EDAMUserException when getting default notebook")
                self.logger.critical(ue)
                return None
        else:
            try:
                self.logger.info("Getting notebooks from Evernote")
                notebooks = self.note_store.listNotebooks()
                self.logger.debug("Found %d notebooks" % len(notebooks))
            except Errors.EDAMUserException, ue:
                self.logger.critical("EDAMUserException when listing notebooks")
                self.logger.critical(ue)
                return None

            self.logger.debug('Iterating over notebooks')
            for n in notebooks:
                if n.name == notebook:
                    return n
            # Haven't found the notebook, create it
            nb = Types.Notebook()
            nb.name = notebook

            try:
                nb = self.note_store.createNotebook(nb)
            except Errors.EDAMUserException, ue:
                self.logger.critical("EDAMUserException creating notebook %s" % notebook)
                self.logger.critical(ue)
                return None
        
        if not nb:
            self.logger.critical("Notebook still isn't defined for some reason")
            return None

        return nb.guid

    def _findOrCreateTags(self):
        "Get or create tags defined in config"
        try:
            self.logger.debug('Tags value from config: %s' % self.config['tags'])
            tags = self.config['tags']
        except KeyError, e:
            self.logger.info("No tags defined in Evernote config") 
            return []
        return self.config['tags']


    def write(self, dataObjs):
        "Write data to Evernote"
        self.logger.debug("Preparing to write Evernote note")
        tags = self._findOrCreateTags()
        if tags:
            self.logger.info("Using tags: %s" % ','.join(tags))
        notebook = self._findOrCreateNotebook()
        if not notebook:
            # TODO: raise a meaningful exception here
            raise Exception('no notebook and this is very informative') 

        self.logger.info("Using notebook: %s" % notebook.name)
        self.logger.debug("%d data objects to write" % len(dataObjs))

        note = Types.Note()
        note.title = "%s - Enslaver Log" % date.today().strftime("%Y-%m-%d")
        self.logger.debug('Title: %s' % note.title)
        note.notebookGuid = notebook.guid
        self.logger.debug('NB Guid: %s' % note.notebookGuid)
        if tags:
            self.logger.debug('Setting note.tagNames to %s' % tags)
            note.tagNames = map(str.strip, tags)

        contentSkel = """<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
        <en-note>%s</en-note>"""

        content = ""

        self.logger.debug('Looping over dataObjs')
        self.logger.debug(type(dataObjs))
        for i in range(len(dataObjs)):
            obj = dataObjs.items()[i][1]
            self.logger.debug(obj)
            if i != 0:
                self.logger.debug('First data object')
                content += "<hr />"
            self.logger.debug('Adding heading')
            content += '<h2>%s</h2>' % obj['config']['heading']
            for d in obj['data'][0]:
                content += '<h3>%s</h3>' % d.title
                content += '<h4>%s</h4>' % d.description
                content += d.enmlContent

        note.content = contentSkel % content

        try:
            note = self.note_store.createNote(note)
        except Errors.EDAMUserException, ue:
            self.logger.critical("EDAMUserException when creating note:")
            self.logger.critical(ue)
            return None

        return note.guid 
