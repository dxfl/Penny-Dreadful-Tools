import os

from discordbot import command, emoji
from magic import card, fetcher_internal, image_fetcher, oracle
from shared import configuration, whoosh_search


# Check that we can fetch card images.
def test_imagedownload():
    filepath = '{dir}/{filename}'.format(dir=configuration.get('image_dir'), filename='island.jpg')
    if fetcher_internal.acceptable_file(filepath):
        os.remove(filepath)
    c = [oracle.load_card('Island')]
    assert image_fetcher.download_image(c) is not None

# Check that we can fall back to the Gatherer images if all else fails.
# Note: bluebones doesn't have Nalathni Dragon, while Gatherer does, which makes it useful here.
def test_fallbackimagedownload():
    filepath = '{dir}/{filename}'.format(dir=configuration.get('image_dir'), filename='nalathni-dragon.jpg')
    if fetcher_internal.acceptable_file(filepath):
        os.remove(filepath)
    c = [oracle.load_card('Nalathni Dragon')]
    assert image_fetcher.download_image(c) is not None

# Check that we can succesfully fail at getting an image.
def test_noimageavailable():
    c = card.Card({'name': "Barry's Land", 'id': 0, 'multiverseid': 0, 'names': "Barry's Land"})
    assert image_fetcher.download_image([c]) is None

# Search for a single card via full name,
def test_solo_query():
    names = command.parse_queries('[Gilder Bairn]')
    assert len(names) == 1
    assert names[0] == 'gilder bairn'
    results = command.results_from_queries(names, whoosh_search.WhooshSearcher())[0]
    assert len(results) == 1

# Two cards, via full name
def test_double_query():
    names = command.parse_queries('[Mother of Runes] [Ghostfire]')
    assert len(names) == 2
    results = command.results_from_queries(names, whoosh_search.WhooshSearcher())
    assert len(results) == 2

# The following two sets assume that Kamahl is a long dead character, and is getting no new cards.
# If wizards does an Onslaught/Odyssey throwback in some supplemental product, they may start failing.
def test_legend_query():
    names = command.parse_queries('[Kamahl]')
    assert len(names) == 1
    results = command.results_from_queries(names, whoosh_search.WhooshSearcher())[0]
    assert len(results.get_ambiguous_matches()) == 2

def test_partial_query():
    names = command.parse_queries("[Kamahl's]")
    assert len(names) == 1
    results = command.results_from_queries(names, whoosh_search.WhooshSearcher())[0]
    assert len(results.get_ambiguous_matches()) == 3

# Check that the list of legal cards is being fetched correctly.
def test_legality_list():
    legal_cards = oracle.legal_cards()
    assert len(legal_cards) > 0

def test_legality_emoji():
    legal_cards = oracle.legal_cards()
    assert len(legal_cards) > 0
    legal_card = oracle.load_card('island')
    assert emoji.legal_emoji(legal_card) == ':white_check_mark:'
    illegal_card = oracle.load_card('black lotus')
    assert emoji.legal_emoji(illegal_card) == ':no_entry_sign:'
    assert emoji.legal_emoji(illegal_card, True) == ':no_entry_sign: (not legal in PD)'

def test_accents():
    c = oracle.load_card('Lim-Dûl the Necromancer')
    assert c is not None
    c = oracle.load_card('Séance')
    assert c is not None
    c = oracle.load_card('Lim-Dul the Necromancer')
    assert c is not None
    c = oracle.load_card('Seance')
    assert c is not None

def test_aether():
    c = oracle.load_card('aether Spellbomb')
    assert c is not None

def test_split_cards():
    cards = oracle.load_cards(['Armed // Dangerous'])
    assert len(cards) == 1
    assert image_fetcher.download_image(cards) is not None
    names = command.parse_queries('[Toil // Trouble]')
    assert len(names) == 1
    results = command.results_from_queries(names, whoosh_search.WhooshSearcher())[0]
    assert len(results) == 1

def test_some_names():
    cards = oracle.search(' of the Reliquary')
    assert('Knight of the Reliquary' in [c.name for c in cards])
    cards = oracle.search('Séance')
    assert('Séance' in [c.name for c in cards])
    cards = oracle.search('Seance')
    assert('Séance' in [c.name for c in cards])
    cards = oracle.search('sean')
    assert('Séance' in [c.name for c in cards])
    cards = oracle.search('Jötun Grunt')
    assert('Jötun Grunt' in [c.name for c in cards])
    cards = oracle.search('Jotun Grunt')
    assert('Jötun Grunt' in [c.name for c in cards])
    cards = oracle.search('Chittering Host')
    assert('Graf Rats' in [c.name for c in cards])
    assert('Midnight Scavengers' in [c.name for c in cards])
    cards = oracle.search('Wastes')
    assert('Wastes' in [c.name for c in cards])
