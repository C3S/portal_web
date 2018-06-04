# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

from pyramid.renderers import render

from ...models import Content


class UncommitedContentWidget():

    def __init__(self, request, category='all'):
        self.party = request.party.id
        self.template = '../../templates/widgets/uncommited_content.pt'
        self.category = category

    def get_len(self, content_list):
        if content_list:
            return len(content_list)
        else:
            return 0

    def output(self):
        uncomm = self.get_len(
            Content.search_uncommits(self.party, self.category))
        output = render(
            self.template,
            {'uncomm': uncomm}
        )
        return output
