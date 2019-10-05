portal_web
=========================

Web portal including:

- Tryton wrapper
- Web user management
- Web frontend
- API
- Plugin system

For a working development setup, see https://github.com/C3S/collecting_society_docker


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

Explanation
```````````

- **.pot**: "Portable Object Template" file, list of message identifiers, template for **.po** files
- **.po**: "Portable Object" file, human editable list of translated messages
- **.mo**: "Machine Object" file, machine readable list of messages, created from a **.po** file

Installation
````````````

- **poedit**: ``$apt-get install poedit``
- **gettext**: ``$apt-get install gettext``
- **lingua**: ``$pip install lingua``

**Note**: If you are running different python versions on the host, you need to ensure, that the right ``pip`` (e.g. ``pip2.7``) is called.

Updates
```````

e.g. for project **portal_web** and language **de**

- only once, to start translation of a project, create the **.pot** file for the project
    - ``$cd collecting_society_docker/volumes/shared/src/portal_web``
    - ``$mkdir portal_web/locale``
    - ``$pot-create -o portal_web/locale/portal_web.pot portal_web``
- only once, if you need a new language, create the **.po** file for the language
    - ``$cd collecting_society_docker/volumes/shared/src/portal_web/portal_web/locale``
    - ``$mkdir -p de/LC_MESSAGES``
    - ``$msginit -l de -o de/LC_MESSAGES/portal_web.po``
- each time, the code or templates changed, recreate the **.pot** file:
    - ``$cd collecting_society_docker/volumes/shared/src/portal_web``
    - ``$pot-create -o portal_web/locale/portal_web.pot portal_web``
- every time the **.pot** file changed, recreate the **.po** files for all languages
    - ``$cd collecting_society_docker/volumes/shared/src/portal_web``
    - ``$msgmerge --update portal_web/locale/*/LC_MESSAGES/portal_web.po portal_web/locale/portal_web.pot``
- to edit translations, change the **.po** file via poedit
    - ``$cd collecting_society_docker/volumes/shared/src/portal_web``
    - ``$poedit portal_web/locale/de/LC_MESSAGES/portal_web.po``
- every time the **.po** file changed, create a **.mo** file
    - ``$cd collecting_society_docker/volumes/shared/src/portal_web``
    - ``$msgfmt -o portal_web/locale/de/LC_MESSAGES/portal_web.mo portal_web/locale/de/LC_MESSAGES/portal_web.po``

Further information
```````````````````

- see `pyramid documentation <http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/i18n.html#working-with-gettext-translation-files>`_


Copyright / License
-------------------

For infos on copyright and licenses, see ``./COPYRIGHT.rst``
