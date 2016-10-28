import json

DEFAULTS = {
    'card_alias_file': './card_aliases.tsv',
    'database': './db',
    'decksite_database': './decksite.db',
    'image_dir': '.',
    'pricesdb': './prices.db',
    'spellfix': './spellfix',
    'to_username': '',
    'to_password': ''
}

def get(key):
    try:
        cfg = json.load(open('config.json'))
    except FileNotFoundError:
        cfg = {}
    if key in cfg:
        return cfg[key]
    else:
        # Lock in the default value if we use it.
        cfg[key] = DEFAULTS[key]
        fh = open('config.json', 'w')
        fh.write(json.dumps(cfg, indent=4))
    return DEFAULTS[key]