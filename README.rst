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


Copyright / Licence
-------------------

For infos on copyright and licenses, see ``./COPYRIGHT.rst``
