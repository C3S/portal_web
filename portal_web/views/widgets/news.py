# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

from pyramid.renderers import render

from ...services import _


def news_widget(request):
    heading = _('News')
    body = render(
        '../../templates/widgets/news.pt',
        {'news': request.context.registry['content']['news']},
        request=request
    )
    return {'heading': heading, 'body': body}
