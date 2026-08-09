import re
import unicodedata

RANKING_DATE = "20 July 2026"
RANKED_TEAMS = ['Spain', 'Argentina', 'France', 'England', 'Brazil', 'Morocco', 'Portugal', 'Belgium', 'Netherlands', 'Mexico', 'Colombia', 'Germany', 'Croatia', 'Switzerland', 'Italy', 'USA', 'Japan', 'Senegal', 'Norway', 'Uruguay', 'Denmark', 'Iran', 'Austria', 'Egypt', 'Ecuador', 'Nigeria', 'Turkiye', 'Australia', 'Algeria', 'Canada', 'Ivory Coast', 'South Korea', 'Ukraine', 'Paraguay', 'Russia', 'Poland', 'Sweden', 'Wales', 'Hungary', 'Serbia', 'DR Congo', 'Scotland', 'Cameroon', 'Panama', 'Slovakia', 'Greece', 'Venezuela', 'Czechia', 'Chile', 'Peru', 'Costa Rica', 'Romania', 'Mali', 'South Africa', 'Ireland', 'Slovenia', 'Tunisia', 'Saudi Arabia', 'Qatar', 'Uzbekistan', 'Bosnia and Herzegovina', 'Burkina Faso', 'Iraq', 'Cape Verde', 'Ghana', 'Honduras', 'Albania', 'UAE', 'North Macedonia', 'Northern Ireland', 'Jamaica', 'Georgia', 'Jordan', 'Iceland', 'Finland', 'Israel', 'Bolivia', 'Kosovo', 'Oman', 'Montenegro', 'Guinea', 'Curacao', 'Syria', 'Gabon', 'Bulgaria', 'New Zealand', 'Angola', 'Haiti', 'Uganda', 'Zambia', 'China', 'Bahrain', 'Benin', 'Thailand', 'Palestine', 'Belarus', 'Guatemala', 'Luxembourg', 'Vietnam', 'El Salvador', 'Tajikistan', 'Trinidad and Tobago', 'Mozambique', 'Madagascar', 'Equatorial Guinea', 'Kyrgyzstan', 'Armenia', 'Comoros', 'Kenya', 'Libya', 'Kazakhstan', 'Tanzania', 'Mauritania', 'Niger', 'Lebanon', 'Gambia', 'Sudan', 'Indonesia', 'Togo', 'North Korea', 'Namibia', 'Sierra Leone', 'Faroe Islands', 'Cyprus', 'Suriname', 'Azerbaijan', 'Estonia', 'Rwanda', 'Malawi', 'Zimbabwe', 'Nicaragua', 'Guinea-Bissau', 'Kuwait', 'Congo', 'Philippines', 'Malaysia', 'Latvia', 'India', 'Central African Republic', 'Liberia', 'Turkmenistan', 'Burundi', 'Ethiopia', 'Dominican Republic', 'Yemen', 'Lesotho', 'Botswana', 'Singapore', 'Lithuania', 'Guyana', 'New Caledonia', 'St. Kitts and Nevis', 'Solomon Islands', 'Puerto Rico', 'Fiji', 'Hong Kong', 'Tahiti', 'Myanmar', 'Moldova', 'Vanuatu', 'Malta', 'Antigua and Barbuda', 'Grenada', 'Cuba', 'Eswatini', 'Saint Lucia', 'Bermuda', 'Papua New Guinea', 'South Sudan', 'Saint Vincent and The Grenadines', 'Afghanistan', 'Andorra', 'Maldives', 'Chinese Taipei', 'Cambodia', 'Montserrat', 'Nepal', 'Mauritius', 'Barbados', 'Belize', 'Bangladesh', 'Dominica', 'Chad', 'Eritrea', 'Laos', 'Cook Islands', 'Sri Lanka', 'Samoa', 'Aruba', 'Mongolia', 'American Samoa', 'Bhutan', 'Macao', 'Brunei', 'Sao Tome and Principe', 'Djibouti', 'Cayman Islands', 'Pakistan', 'Somalia', 'Tonga', 'Timor-Leste', 'Gibraltar', 'Guam', 'Seychelles', 'Turks and Caicos Islands', 'Liechtenstein', 'Bahamas', 'U.S. Virgin Islands', 'British Virgin Islands', 'Anguilla', 'San Marino']

CONFEDERATIONS = {'AFC': ['Afghanistan', 'Australia', 'Bahrain', 'Bangladesh', 'Bhutan', 'Brunei', 'Cambodia', 'China', 'Chinese Taipei', 'Guam', 'Hong Kong', 'India', 'Indonesia', 'Iran', 'Iraq', 'Japan', 'Jordan', 'Kuwait', 'Kyrgyzstan', 'Laos', 'Lebanon', 'Macao', 'Malaysia', 'Maldives', 'Mongolia', 'Myanmar', 'Nepal', 'North Korea', 'Oman', 'Pakistan', 'Palestine', 'Philippines', 'Qatar', 'Saudi Arabia', 'Singapore', 'South Korea', 'Sri Lanka', 'Syria', 'Tajikistan', 'Thailand', 'Timor-Leste', 'Turkmenistan', 'UAE', 'Uzbekistan', 'Vietnam', 'Yemen'], 'CAF': ['Algeria', 'Angola', 'Benin', 'Botswana', 'Burkina Faso', 'Burundi', 'Cameroon', 'Cape Verde', 'Central African Republic', 'Chad', 'Comoros', 'Congo', 'DR Congo', 'Ivory Coast', 'Djibouti', 'Egypt', 'Equatorial Guinea', 'Eritrea', 'Eswatini', 'Ethiopia', 'Gabon', 'Gambia', 'Ghana', 'Guinea', 'Guinea-Bissau', 'Kenya', 'Lesotho', 'Liberia', 'Libya', 'Madagascar', 'Malawi', 'Mali', 'Mauritania', 'Mauritius', 'Morocco', 'Mozambique', 'Namibia', 'Niger', 'Nigeria', 'Rwanda', 'Sao Tome and Principe', 'Senegal', 'Seychelles', 'Sierra Leone', 'Somalia', 'South Africa', 'South Sudan', 'Sudan', 'Tanzania', 'Togo', 'Tunisia', 'Uganda', 'Zambia', 'Zimbabwe'], 'CONCACAF': ['Anguilla', 'Antigua and Barbuda', 'Aruba', 'Bahamas', 'Barbados', 'Belize', 'Bermuda', 'British Virgin Islands', 'Canada', 'Cayman Islands', 'Costa Rica', 'Cuba', 'Curacao', 'Dominica', 'Dominican Republic', 'El Salvador', 'Grenada', 'Guatemala', 'Guyana', 'Haiti', 'Honduras', 'Jamaica', 'Mexico', 'Montserrat', 'Nicaragua', 'Panama', 'Puerto Rico', 'St. Kitts and Nevis', 'Saint Lucia', 'Saint Vincent and The Grenadines', 'Suriname', 'Trinidad and Tobago', 'Turks and Caicos Islands', 'U.S. Virgin Islands', 'USA'], 'CONMEBOL': ['Argentina', 'Bolivia', 'Brazil', 'Chile', 'Colombia', 'Ecuador', 'Paraguay', 'Peru', 'Uruguay', 'Venezuela'], 'OFC': ['American Samoa', 'Cook Islands', 'Fiji', 'New Caledonia', 'New Zealand', 'Papua New Guinea', 'Samoa', 'Solomon Islands', 'Tahiti', 'Tonga', 'Vanuatu'], 'UEFA': ['Albania', 'Andorra', 'Armenia', 'Austria', 'Azerbaijan', 'Belarus', 'Belgium', 'Bosnia and Herzegovina', 'Bulgaria', 'Croatia', 'Cyprus', 'Czechia', 'Denmark', 'England', 'Estonia', 'Faroe Islands', 'Finland', 'France', 'Georgia', 'Germany', 'Gibraltar', 'Greece', 'Hungary', 'Iceland', 'Ireland', 'Israel', 'Italy', 'Kazakhstan', 'Kosovo', 'Latvia', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Malta', 'Moldova', 'Montenegro', 'Netherlands', 'North Macedonia', 'Northern Ireland', 'Norway', 'Poland', 'Portugal', 'Romania', 'Russia', 'San Marino', 'Scotland', 'Serbia', 'Slovakia', 'Slovenia', 'Spain', 'Sweden', 'Switzerland', 'Turkiye', 'Ukraine', 'Wales']}

FLAG_CODES = {'Spain': 'es', 'Argentina': 'ar', 'France': 'fr', 'England': 'gb-eng', 'Brazil': 'br', 'Morocco': 'ma', 'Portugal': 'pt', 'Belgium': 'be', 'Netherlands': 'nl', 'Mexico': 'mx', 'Colombia': 'co', 'Germany': 'de', 'Croatia': 'hr', 'Switzerland': 'ch', 'Italy': 'it', 'USA': 'us', 'Japan': 'jp', 'Senegal': 'sn', 'Norway': 'no', 'Uruguay': 'uy', 'Denmark': 'dk', 'Iran': 'ir', 'Austria': 'at', 'Egypt': 'eg', 'Ecuador': 'ec', 'Nigeria': 'ng', 'Turkiye': 'tr', 'Australia': 'au', 'Algeria': 'dz', 'Canada': 'ca', 'Ivory Coast': 'ci', 'South Korea': 'kr', 'Ukraine': 'ua', 'Paraguay': 'py', 'Russia': 'ru', 'Poland': 'pl', 'Sweden': 'se', 'Wales': 'gb-wls', 'Hungary': 'hu', 'Serbia': 'rs', 'DR Congo': 'cd', 'Scotland': 'gb-sct', 'Cameroon': 'cm', 'Panama': 'pa', 'Slovakia': 'sk', 'Greece': 'gr', 'Venezuela': 've', 'Czechia': 'cz', 'Chile': 'cl', 'Peru': 'pe', 'Costa Rica': 'cr', 'Romania': 'ro', 'Mali': 'ml', 'South Africa': 'za', 'Ireland': 'ie', 'Slovenia': 'si', 'Tunisia': 'tn', 'Saudi Arabia': 'sa', 'Qatar': 'qa', 'Uzbekistan': 'uz', 'Bosnia and Herzegovina': 'ba', 'Burkina Faso': 'bf', 'Iraq': 'iq', 'Cape Verde': 'cv', 'Ghana': 'gh', 'Honduras': 'hn', 'Albania': 'al', 'UAE': 'ae', 'North Macedonia': 'mk', 'Northern Ireland': 'gb-nir', 'Jamaica': 'jm', 'Georgia': 'ge', 'Jordan': 'jo', 'Iceland': 'is', 'Finland': 'fi', 'Israel': 'il', 'Bolivia': 'bo', 'Kosovo': 'xk', 'Oman': 'om', 'Montenegro': 'me', 'Guinea': 'gn', 'Curacao': 'cw', 'Syria': 'sy', 'Gabon': 'ga', 'Bulgaria': 'bg', 'New Zealand': 'nz', 'Angola': 'ao', 'Haiti': 'ht', 'Uganda': 'ug', 'Zambia': 'zm', 'China': 'cn', 'Bahrain': 'bh', 'Benin': 'bj', 'Thailand': 'th', 'Palestine': 'ps', 'Belarus': 'by', 'Guatemala': 'gt', 'Luxembourg': 'lu', 'Vietnam': 'vn', 'El Salvador': 'sv', 'Tajikistan': 'tj', 'Trinidad and Tobago': 'tt', 'Mozambique': 'mz', 'Madagascar': 'mg', 'Equatorial Guinea': 'gq', 'Kyrgyzstan': 'kg', 'Armenia': 'am', 'Comoros': 'km', 'Kenya': 'ke', 'Libya': 'ly', 'Kazakhstan': 'kz', 'Tanzania': 'tz', 'Mauritania': 'mr', 'Niger': 'ne', 'Lebanon': 'lb', 'Gambia': 'gm', 'Sudan': 'sd', 'Indonesia': 'id', 'Togo': 'tg', 'North Korea': 'kp', 'Namibia': 'na', 'Sierra Leone': 'sl', 'Faroe Islands': 'fo', 'Cyprus': 'cy', 'Suriname': 'sr', 'Azerbaijan': 'az', 'Estonia': 'ee', 'Rwanda': 'rw', 'Malawi': 'mw', 'Zimbabwe': 'zw', 'Nicaragua': 'ni', 'Guinea-Bissau': 'gw', 'Kuwait': 'kw', 'Congo': 'cg', 'Philippines': 'ph', 'Malaysia': 'my', 'Latvia': 'lv', 'India': 'in', 'Central African Republic': 'cf', 'Liberia': 'lr', 'Turkmenistan': 'tm', 'Burundi': 'bi', 'Ethiopia': 'et', 'Dominican Republic': 'do', 'Yemen': 'ye', 'Lesotho': 'ls', 'Botswana': 'bw', 'Singapore': 'sg', 'Lithuania': 'lt', 'Guyana': 'gy', 'New Caledonia': 'nc', 'St. Kitts and Nevis': 'kn', 'Solomon Islands': 'sb', 'Puerto Rico': 'pr', 'Fiji': 'fj', 'Hong Kong': 'hk', 'Tahiti': 'pf', 'Myanmar': 'mm', 'Moldova': 'md', 'Vanuatu': 'vu', 'Malta': 'mt', 'Antigua and Barbuda': 'ag', 'Grenada': 'gd', 'Cuba': 'cu', 'Eswatini': 'sz', 'Saint Lucia': 'lc', 'Bermuda': 'bm', 'Papua New Guinea': 'pg', 'South Sudan': 'ss', 'Saint Vincent and The Grenadines': 'vc', 'Afghanistan': 'af', 'Andorra': 'ad', 'Maldives': 'mv', 'Chinese Taipei': 'tw', 'Cambodia': 'kh', 'Montserrat': 'ms', 'Nepal': 'np', 'Mauritius': 'mu', 'Barbados': 'bb', 'Belize': 'bz', 'Bangladesh': 'bd', 'Dominica': 'dm', 'Chad': 'td', 'Eritrea': 'er', 'Laos': 'la', 'Cook Islands': 'ck', 'Sri Lanka': 'lk', 'Samoa': 'ws', 'Aruba': 'aw', 'Mongolia': 'mn', 'American Samoa': 'as', 'Bhutan': 'bt', 'Macao': 'mo', 'Brunei': 'bn', 'Sao Tome and Principe': 'st', 'Djibouti': 'dj', 'Cayman Islands': 'ky', 'Pakistan': 'pk', 'Somalia': 'so', 'Tonga': 'to', 'Timor-Leste': 'tl', 'Gibraltar': 'gi', 'Guam': 'gu', 'Seychelles': 'sc', 'Turks and Caicos Islands': 'tc', 'Liechtenstein': 'li', 'Bahamas': 'bs', 'U.S. Virgin Islands': 'vi', 'British Virgin Islands': 'vg', 'Anguilla': 'ai', 'San Marino': 'sm', 'Greenland': 'gl', 'Northern Mariana Islands': 'mp', 'Tuvalu': 'tv', 'Marshall Islands': 'mh'}

EXTRA_TEAMS = {
    "Greenland": "CONCACAF",
    "Northern Mariana Islands": "AFC",
    "Tuvalu": "OFC",
    "Marshall Islands": "OFC",
}

SLOT_CONFIG = {
    "AFC": {"direct": 8, "playoff": 1},
    "CAF": {"direct": 9, "playoff": 1},
    "CONCACAF": {"direct": 6, "playoff": 2},
    "CONMEBOL": {"direct": 6, "playoff": 1},
    "OFC": {"direct": 1, "playoff": 1},
    "UEFA": {"direct": 16, "playoff": 0},
}

def _slug(text):
    value = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value

def _code(name, used):
    letters = re.sub(r"[^A-Za-z]", "", name).upper()
    base = (letters[:3] or "T").ljust(3, "X")
    code = base
    i = 2
    while code in used:
        code = (base[:2] + str(i))[:3]
        i += 1
    used.add(code)
    return code

_rank = {name: i + 1 for i, name in enumerate(RANKED_TEAMS)}
_confed = {}
for confed, names in CONFEDERATIONS.items():
    for name in names:
        _confed[name] = confed

_used_codes = set()
TEAMS = []
for name in RANKED_TEAMS:
    TEAMS.append({
        "id": _slug(name),
        "name": name,
        "code": _code(name, _used_codes),
        "confederation": _confed[name],
        "fifaRank": _rank[name],
        "rankingLabel": f"#{_rank[name]}",
        "flagCode": FLAG_CODES[name],
        "isFifaMember": True,
    })

for offset, (name, confed) in enumerate(EXTRA_TEAMS.items(), start=212):
    TEAMS.append({
        "id": _slug(name),
        "name": name,
        "code": _code(name, _used_codes),
        "confederation": confed,
        "fifaRank": None,
        "effectiveRank": offset,
        "rankingLabel": "NR",
        "flagCode": FLAG_CODES[name],
        "isFifaMember": False,
    })

TEAM_BY_ID = {team["id"]: team for team in TEAMS}
