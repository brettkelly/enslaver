ENslaver
========

A Python clone of Brett Terpstra's [Slogger](https://github.com/ttscoff/Slogger) project that logs to Evernote

This is a work in progress.

You'll need:

* An account on the Evernote [Sandbox](https://sandbox.evernote.com) (dev server)
* A developer token from Sandbox ([get that here](https://sandbox.evernote.com/api/DeveloperToken.action))
* The `evernote` and `feedparser` libs installed (both are available via `pip`)

#### Setup

(I'll eventually automate this stuff, but for now you have to do it manually)

* Add your developer token to a file called `.entoken` in the project directory
* Modify `.enslaver` in the project directory to use your own accounts and such for social services.
* This repo gitignores the logs directory, so make sure you create a `logs` dir alongside `enslaver.py`

#### Known issues

* This thing barely works at all
* It has one working plugin
* The logger facility gets more action than, well, something that gets a lot of action

I've got a handful of things in the `TODO` file that I hope to get to (other than writing a buttload of other plugins)

Feel free to fork, send pull requests, the whole shebang. 

Heaven help you.
