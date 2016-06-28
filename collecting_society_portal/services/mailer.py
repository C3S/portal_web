# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

import logging
import quopri

from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message

log = logging.getLogger(__name__)


def send_mail(request, subject, sender, recipients, body):
    mailer = get_mailer(request)
    message = Message(
        subject=subject,
        sender=sender,
        recipients=recipients,
        body=body
    )
    mailer.send_immediately(message, fail_silently=False)
    log.debug(quopri.decodestring(message.to_message().__str__()))
