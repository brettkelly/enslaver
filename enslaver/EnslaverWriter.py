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
        self.client = client
        self.logger = logger

    def _findOrCreateNotebook(self):
        useDefault = False
        try:
            notebook = config['notebook']
        except KeyError, e:
            self.logger.info("Notebook not defined in config; using default notebook")
            useDefault = True
        
        if useDefault:
            try:
                nb = note_store.getDefaultNotebook()
            except EDAMUserException, ue:
                self.logger.critical("EDAMUserException when getting default notebook")
                self.logger.critical(ue)
                return None
        else:
            try:
                self.logger.info("Getting notebooks from Evernote")
                notebooks = self.client.note_store.listNotebooks()
                self.logger.debug("Found %d notebooks" % len(notebooks))
            except Errors.EDAMUserException, ue:
                self.logger.critical("EDAMUserException when listing notebooks")
                self.logger.critical(ue)
                return None
            for n in notebooks:
                if n.name == notebook:
                    return n.guid
            # Haven't found the notebook, create it
            nb = Types.Notebook()
            nb.name = notebook

            try:
                nb = note_store.createNotebook(nb)
            except EDAMUserException, ue:
                self.logger.critical("EDAMUserException creating notebook %s" % notebook)
                self.logger.critical(ue)
                return None
        
        if not nb:
            self.logger.critical("Notebook still isn't defined for some reason")
            return None

        return nb.guid

    def _findOrCreateTags(self):
        "Get or create tags defined in config"
        noteTags = []
        try:
            tags = config['tags']
        except KeyError, e:
            self.logger.info("No tags defined in Evernote config") 
            return None

        try:
            tagList = note_store.listTags()
        except EDAMUserException, ue:
            self.logger.critical("EDAMUserException getting tag list")
            self.logger.critical(ue)
            return None

        for tag in tagList:
            if tag.name in tags:
                noteTags.append(tag)
                taglist.remove(tag.name)

        for tag in tags:
            try:
                t = Types.Tag()
                t.name = tag
                newTag = note_store.createTag(t)
                noteTags.append(newTag)
            except EDAMUserException, ue:
                self.logger.critical("EDAMUserException getting tag list")
                self.logger.critical(ue)
                self.logger.info("Skipping tag: %s" % tag)
        
        return noteTags

    def write(self, dataObjs):
        "Write data to Evernote"
        self.logger.debug("Preparing to write Evernote note")
        tags = self._findOrCreateTags()
        self.logger.info("Using tags: %s" % [t.name for t in tags].join(', '))
        notebook = self._findOrCreateNotebook()
        if not notebook:
            # TODO: raise a meaningful exception here
            raise Exception('no notebook and this is very informative') 

        self.logger.info("Using notebook: %s" % notebook.name)
        self.logger.debug("%d data objects to write" % len(dataObjs))

        note = Types.Note()
        note.title = "%s - Enslaver Log" % date.today().strftime("%Y-%m-%d")
        note.notebookGuid = notebook.guid
        note.tagGuids = [t.guid for t in tags]

        contentSkel = """<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
        contentSkel += "<en-note>%s</en-note>"""

        
