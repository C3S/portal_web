# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

import os
import logging
import quopri

from pyramid_mailer import get_mailer
from pyramid_mailer.mailer import Mailer
from pyramid_mailer.message import Message

from ..config import get_plugins

log = logging.getLogger(__name__)


def get_locale(request):
    locale = request._LOCALE_
    languages = request.registry.settings['app.languages'].split(' ')
    return locale if locale in languages else 'en'


def get_template_paths(request):
    paths = []

    # portal
    paths.append(
        os.path.join(os.path.dirname(__file__), '..', 'templates', 'mail')
    )

    # portal plugins
    plugins = get_plugins(request.registry.settings)
    for priority in sorted(plugins):
        paths.append(
            os.path.join(
                plugins[priority]['path'], plugins[priority]['name'],
                'templates', 'mail'
            )
        )

    return paths


def get_template_raw(paths, filename):
    for path in paths:
        file = os.path.join(path, filename)
        if os.path.isfile(file):
            with open(file, 'rb') as f:
                return {
                    'subject': f.readline().rstrip().decode('utf-8'),
                    'body': f.read().decode('utf-8')
                }
    return False


def get_content(request, template, variables={}):
    paths = get_template_paths(request)
    filename = template + '.' + get_locale(request) + '.txt'
    raw = get_template_raw(paths, filename)
    if not raw:
        return False
    return {
        'subject': raw['subject'].format(**variables),
        'body': raw['body'].format(**variables)
    }


def send_mail(request, template, variables={}, *args, **kwargs):
    settings = request.registry.settings
    mailer = get_mailer(request)

    # template content
    content = get_content(request, template, variables)
    if not content:
        log.info(
            'Error sending mail template %s with variables %s' % (
                template, variables
            )
        )
        return False

    # sender
    if 'sender' not in kwargs and 'mail.default_sender' in settings:
        kwargs['sender'] = settings['mail.default_sender']

    # subject
    if 'subject' not in kwargs:
        kwargs['subject'] = content['subject']

    # body
    if 'body' not in kwargs:
        kwargs['body'] = content['body']

    # create and send message
    message = Message(*args, **kwargs)
    mailer.send(message)

    # log message to debug console
    log.debug(quopri.decodestring(message.to_message().__str__()))
