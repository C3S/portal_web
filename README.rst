collecting_society.portal
=========================

Web portal including:

- Tryton wrapper
- Web user management
- Web frontend
- API
- Plugin system

For a working development setup, see https://github.com/C3S/c3s.ado


Tryton wrapper
--------------

Provides helpful methods for initialisation of the db connection, transaction 
handling, communication with the tryton pool and wrapping of tryton models.
Includes tryton model wrappers for web_user, company and bank_account_number.


Web user management
-------------------

Enables authorization and authentication of web user (register, login).


Web frontend
------------

Provides a bootstrap based basic user front- and backend, a traversal based
registry for hierarchical content structures and a form controller for easy
handling of multiple forms per view and maintainance of complex forms.


API
---

Provides an include mechanism for an API either within the web frontend or
standalone.


Plugin system
-------------

Plugins are other minimal setup pyramid apps, wich will be included within
the main app. Plugins may extend and possibly override certain aspects
of the main app. The plugins are found by a shared egg name pattern
configured within settings (``plugins.pattern``).

They have to define in their settings:

- ``plugin.priority=<Integer>``: to ensure a well defined order of inclusion

They should define in their ``__init__.py``:

- ``include_resources(settings)``: for all additions and changes to resources
- ``include views(settings)``: for all registrations of views

Settings
''''''''

The settings of plugins extend and override the main settings. Those of
plugins with the heigher priority will override lower ones.

Views
'''''

The views of plugins with higher priority will be registered first, later
ones will be ignored.

Resources
'''''''''

Resources of plugins may be added to main ones with ``Resource.add()``

Registry within resources may be extended with ``Resource.extend_registry()``

Logging
'''''''

The logging configuration of plugins will spawn new logger


Translations
------------

Language detection from browser settings and browser session handling for language should be implemented already. The only thing missing is the language switch and an update of the hard coded list of available language (to prevent exposing unfinished content).

The following part is an update from the [readme of the ticketing project](https://github.com/C3S/c3sPartyTicketing/blob/C3Sevents14001/README.i18n.rst#lingua-23) and should be included within the README.rst files of all projects (portal, portal.creative, portal.imp) with right paths set. Please update them as well, when you add the initial translations to the repository, or give the ticket back to me afterwards. I have not done the initial steps as I recommend you to do it yourself once to get the concept.

One last note concerning the workflow: Usually, translators will just update the .po file and hand it back (or might add/change translations online via http://pootle.c3s.cc/), and someone of our staff has to do the updates of the .pot file, the review of translations and the compiling into the .mo file.

---

# Explanation

- **.pot**: "Portable Object Template" file, list of message identifiers, template for **.po** files
- **.po**: "Portable Object" file, human editable list of translated messages
- **.mo**: "Machine Object" file, machine readable list of messages, created from a **.po** file

# Installation

- **poedit**: ``$apt-get install poedit``
- **gettext**: ``$apt-get install gettext``
- **lingua**: ``$pip install lingua``

**Note**: If you are running different python versions on the host, you need to ensure, that the right ``pip`` (e.g. ``pip2.7``) is called.

# Updates

e.g. for project **collecting_society.portal** and language **de**

## only once, to start translation of a project, create the **.pot** file for the project

- ``$cd c3s.ado/ado/src/collecting_society.portal``
- ``$mkdir collecting_society_portal/locale``
- ``$pot-create -o collecting_society_portal/locale/collecting_society_portal.pot collecting_society_portal``

## only once, if you need a new language, create the **.po** file for the language

- ``$cd c3s.ado/ado/src/collecting_society.portal/collecting_society_portal/locale``
- ``$mkdir -p de/LC_MESSAGES``
- ``$msginit -l de -o de/LC_MESSAGES/collecting_society_portal.po``

## each time, the code or templates changed, recreate the **.pot** file:

- ``$cd c3s.ado/ado/src/collecting_society.portal``
- ``$pot-create -o collecting_society_portal/locale/collecting_society_portal.pot collecting_society_portal``

## every time the **.pot** file changed, recreate the **.po** files for all languages

- ``$cd c3s.ado/ado/src/collecting_society.portal``
- ``$msgmerge --update collecting_society_portal/locale/*/LC_MESSAGES/collecting_society_portal.po collecting_society_portal/locale/collecting_society_portal.pot``

## to edit translations, change the **.po** file via poedit

- ``$cd c3s.ado/ado/src/collecting_society.portal``
- ``$poedit collecting_society_portal/locale/de/LC_MESSAGES/collecting_society_portal.po``

## every time the **.po** file changed, create a **.mo** file

- ``$cd c3s.ado/ado/src/collecting_society.portal``
- ``$msgfmt -o collecting_society_portal/locale/de/LC_MESSAGES/collecting_society_portal.mo collecting_society_portal/locale/de/LC_MESSAGES/collecting_society_portal.po``

# Further information

- see [pyramid documentation](http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/i18n.html#working-with-gettext-translation-files)


Copyright / License
-------------------

For infos on copyright and licenses, see ``./COPYRIGHT.rst``
