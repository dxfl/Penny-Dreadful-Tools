from typing import Dict, List

from magic import card, fetcher, mana, multiverse, rotation
from magic.database import db
from shared.database import sqlescape
from shared.pd_exception import InvalidDataException, TooFewItemsException

# Primary public interface to the magic package. Call `oracle.init()` after setting up application context and before using any methods.

LEGAL_CARDS: List[str] = []
CARDS_BY_NAME: Dict[str, card.Card] = {}

def init():
    if len(CARDS_BY_NAME) == 0:
        for c in load_cards():
            CARDS_BY_NAME[c.name] = c

def search(query):
    like_query = '%{query}%'.format(query=card.canonicalize(query))
    sql = """
        {base_query}
        HAVING name_ascii LIKE %s OR names LIKE %s
        ORDER BY pd_legal DESC, name
    """.format(base_query=multiverse.base_query())
    rs = db().execute(sql, [like_query, like_query])
    return [card.Card(r) for r in rs]

def valid_name(name):
    if name in CARDS_BY_NAME:
        return name
    else:
        canonicalized = card.canonicalize(name)
        for k in CARDS_BY_NAME:
            if canonicalized == card.canonicalize(k):
                return k
    raise InvalidDataException('Did not find any cards looking for `{name}`'.format(name=name))

def load_card(name):
    return CARDS_BY_NAME.get(name, load_cards([name])[0])

def load_cards(names=None, where=None):
    if names:
        names = set(names)
    if names:
        names_clause = 'LOWER(c.name) IN ({names})'.format(names=', '.join(sqlescape(name).lower() for name in names))
    else:
        names_clause = '(1 = 1)'
    if where is None:
        where = '(1 = 1)'
    sql = multiverse.cached_base_query('({where} AND {names})'.format(where=where, names=names_clause))
    rs = db().execute(sql)
    if names and len(names) != len(rs):
        missing = names.symmetric_difference([r['name'] for r in rs])
        raise TooFewItemsException('Expected `{namelen}` and got `{rslen}` with `{names}`.  missing=`{missing}`'.format(namelen=len(names), rslen=len(rs), names=names, missing=missing))
    return [card.Card(r) for r in rs]

def cards_by_name():
    return CARDS_BY_NAME

def bugged_cards():
    sql = multiverse.cached_base_query('bugs IS NOT NULL')
    rs = db().execute(sql)
    return [card.Card(r) for r in rs]

def legal_cards(force=False):
    if len(LEGAL_CARDS) == 0 or force:
        new_list = multiverse.set_legal_cards(force)
        if new_list is None:
            sql = 'SELECT bq.name FROM ({base_query}) AS bq WHERE bq.id IN (SELECT card_id FROM card_legality WHERE format_id = {format_id})'.format(base_query=multiverse.base_query(), format_id=multiverse.get_format_id('Penny Dreadful'))
            new_list = [row['name'] for row in db().execute(sql)]
        LEGAL_CARDS.clear()
        for name in new_list:
            LEGAL_CARDS.append(name)
    return LEGAL_CARDS

def get_printings(generalized_card: card.Card):
    sql = 'SELECT ' + (', '.join('p.' + property for property in card.printing_properties())) + ', s.code AS set_code' \
        + ' FROM printing AS p' \
        + ' LEFT OUTER JOIN `set` AS s ON p.set_id = s.id' \
        + ' WHERE card_id = %s '
    rs = db().execute(sql, [generalized_card.id])
    return [card.Printing(r) for r in rs]

def deck_sort(c):
    s = ''
    if c.is_creature():
        s += 'A'
    elif c.is_land():
        s += 'C'
    else:
        s += 'B'
    m = 'A'
    for cost in c.get('mana_cost') or ():
        if mana.has_x(cost):
            m = 'X'
    s += m
    s += str(c.cmc).zfill(10)
    s += c.name
    return s

def scryfall_import(name):
    sfcard = fetcher.internal.fetch_json('https://api.scryfall.com/cards/named?fuzzy={name}'.format(name=name))
    if sfcard['object'] == 'error':
        raise Exception()
    try:
        valid_name(sfcard['name'])
        return False
    except InvalidDataException:
        insert_scryfall_card(sfcard)
        return True

def insert_scryfall_card(sfcard):
    imagename = '{set}_{number}'.format(set=sfcard['set'], number=sfcard['collector_number'])
    c = {
        'layout': sfcard['layout'],
        'cmc': int(float(sfcard['cmc'])),
        'imageName': imagename,
        'legalities': [],
        'printings': [sfcard['set']],
        'rarity': sfcard['rarity'],
        'names': []
    }
    faces = sfcard.get('card_faces', [sfcard])
    names = [face['name'] for face in faces]
    for face in faces:
        tl = face['type_line'].split('—')
        types = tl[0]
        subtypes = tl[1] if len(tl) > 1 else []

        c.update({
            'name': face['name'],
            'type': face['type_line'],
            'types': types, # This technically includes supertypes.
            'subtypes': subtypes,
            'text': face.get('oracle_text', ''),
            'manaCost': face.get('mana_cost', None)
        })
        c['names'] = names
        multiverse.insert_card(c)
    multiverse.update_cache()
    CARDS_BY_NAME[sfcard['name']] = load_card(sfcard['name'])

def last_pd_rotation_changes():
    current_code = rotation.last_rotation_ex()['code']
    previous = multiverse.SEASONS[multiverse.SEASONS.index(current_code) - 1]
    previous_id = multiverse.get_format_id("Penny Dreadful {f}".format(f=previous))
    current_id = multiverse.get_format_id("Penny Dreadful")
    return changes_between_formats(previous_id, current_id)

def changes_between_formats(f1, f2):
    return [query_diff_formats(f2, f1), query_diff_formats(f1, f2)]

def query_diff_formats(f1, f2):
    where = '''
    c.id IN
        (SELECT card_id FROM card_legality
            WHERE format_id = {format1})
    AND c.id NOT IN
        (SELECT card_id FROM card_legality WHERE format_id = {format2})
    '''.format(format1=f1, format2=f2)

    rs = db().execute(multiverse.cached_base_query(where=where))
    out = [card.Card(r) for r in rs]
    return sorted(out, key=lambda card: card['name'])

def if_todays_prices(out=True):
    current_format = multiverse.get_format_id("Penny Dreadful")
    if out:
        not_clause = ''
        compare = '<'
    else:
        not_clause = 'NOT'
        compare = '>='

    where = '''
        c.id {not_clause} IN
            (SELECT card_id FROM card_legality
                WHERE format_id = {format})
        AND c.name in (SELECT name from prices.cache where week {compare} 0.5)
        AND c.layout IN ({layouts})
    '''.format(not_clause=not_clause, format=current_format, compare=compare, layouts=', '.join([sqlescape(k) for k, v in multiverse.layouts().items() if v]))

    rs = db().execute(multiverse.cached_base_query(where=where))
    out = [card.Card(r) for r in rs]
    return sorted(out, key=lambda card: card['name'])
