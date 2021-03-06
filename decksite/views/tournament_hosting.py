from decksite.view import View
from magic import tournaments


# pylint: disable=no-self-use
class TournamentHosting(View):
    def __init__(self):
        hosts = [host for series in tournaments.all_series_info() for host in series['hosts']]
        hosts += ['chaosblackdoom', 'hexalite']
        self.hosts = ', '.join(set(hosts))

    def subtitle(self):
        return 'Tournament Hosting'
