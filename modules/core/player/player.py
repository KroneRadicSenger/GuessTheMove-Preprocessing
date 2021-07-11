from math import ceil
import re

import mechanize
from bs4 import BeautifulSoup


PLAYERS_LIST_URL = 'https://2700chess.com/all-fide-players'
GAMES_LIST_URL = 'https://2700chess.com/games'

# Store retrieved full player names in cache. Initially, this dict contains exception cases in which
# the database would not be able to find the player due to different representations of the names
player_name_cache = {
    'Mamedov, Rau': 'Mamedov, Rauf',
    'Vachier Lagrave, M': 'Vachier-Lagrave, Maxime',
    'Kramnik, V': 'Kramnik, Wladimir Borissowitsch',
    'Narayanan, SL': 'Narayanan, Sunilduth Lyna',
    'Liren, Ding': 'Liren, Ding',
    'Liem, Le Quang': 'Liem, Le Quang',
    'Xiangzhi, Bu': 'Xiangzhi, Bu',
    'Yi, Wei': 'Yi, Wei',
}

# Exceptions where the name is written differently in the database (but not necessarily in the way we
# want to display the player name)
database_player_name_exceptions = {
    'Mamedov, Rau': 'Mamedov, Rau',
    'Liren, Ding': 'Ding Liren',
    'Liem, Le Quang': 'Le Quang Liem',
    'Xiangzhi, Bu': 'Bu Xiangzhi',
    'Yi, Wei': 'Wei Yi',
    'Narayanan, SL': 'Narayanan, S.L',
}


def get_full_player_name(incomplete_player_name):
    if incomplete_player_name in player_name_cache:
        return player_name_cache[incomplete_player_name]

    browser = mechanize.Browser()

    browser.set_handle_robots(False)
    browser.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    browser.open(PLAYERS_LIST_URL)

    browser.select_form(nr=0)
    browser.form['name'] = incomplete_player_name
    browser.form['activity'] = ['']
    response = browser.submit().read()
    soup = BeautifulSoup(response, 'html.parser')

    player_names = soup.select("td[class='name'] span")
    if not player_names:
        print('Could not find complete name for', incomplete_player_name, '. Using input name..')
        full_player_name = incomplete_player_name
    else:
        full_player_name = player_names[0].text

    player_name_cache[incomplete_player_name] = full_player_name
    browser.close()

    return full_player_name


black_elo_pattern = re.compile('BlackElo "([0-9]+)"')
white_elo_pattern = re.compile('WhiteElo "([0-9]+)"')


def get_player_elo_ratings_for_game(analyzed_game):
    if contains_white_player_rating(analyzed_game) and contains_black_player_rating(analyzed_game):
        return analyzed_game['whitePlayerRating'], analyzed_game['blackPlayerRating']

    # Check if elo ratings are included in the pgn
    pgn_white_elo_match = white_elo_pattern.search(analyzed_game['pgn'])
    pgn_black_elo_match = black_elo_pattern.search(analyzed_game['pgn'])
    if pgn_white_elo_match and pgn_black_elo_match:
        return pgn_white_elo_match.group(1), pgn_black_elo_match.group(1)

    # Else: Try to find elo ratings with game database
    grandmaster_side = analyzed_game['gameAnalysis']['grandmasterSide']
    result = '1-0' if grandmaster_side == 'white' else '0-1'

    game_date = analyzed_game['gameInfo']['date']
    if game_date is None or '.' not in game_date:
        game_date_year = ''
    else:
        game_date_year = game_date.split('.')[0]

    moves = str(ceil(len(analyzed_game['gameAnalysis']['analyzedMoves']) / 2))

    browser = mechanize.Browser()

    browser.set_handle_robots(False)
    browser.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    browser.open(GAMES_LIST_URL)

    browser.select_form(nr=0)

    browser.form['s[white_player]'] = get_database_player_name(analyzed_game['whitePlayer'])
    browser.form['s[black_player]'] = get_database_player_name(analyzed_game['blackPlayer'])

    browser.form['s[from_date]'] = game_date_year
    browser.form['s[to_date]'] = game_date_year
    browser.form['s[result]'] = [result]
    browser.form['s[from_moves]'] = moves
    browser.form['s[to_moves]'] = moves
    for checkbox in browser.find_control(type='checkbox').items:
        checkbox.selected = False  # dont ignore colors
    response = browser.submit().read()
    soup = BeautifulSoup(response, 'html.parser')

    white_player_rating = None
    black_player_rating = None

    if contains_white_player_rating(analyzed_game):
        white_player_rating = analyzed_game['whitePlayerRating']
    elif soup.select("td[class='white_elo rating']"):
        white_player_rating = soup.select("td[class='white_elo rating']")[0].text

    if contains_black_player_rating(analyzed_game):
        black_player_rating = analyzed_game['blackPlayerRating']
    elif soup.select("td[class='black_elo rating']"):
        black_player_rating = soup.select("td[class='black_elo rating']")[0].text

    if white_player_rating and black_player_rating:
        browser.close()
        # Elo ratings found
        return white_player_rating, black_player_rating
    else:
        # If no matching game was found, try searching without the opponent name and only match the last name
        return get_uncertain_player_elo_ratings(browser, grandmaster_side, analyzed_game)


# If no game was found, try searching without the opponent name and find a game that contains
# the opponents last name
def get_uncertain_player_elo_ratings(browser, grandmaster_side, analyzed_game):
    browser.select_form(nr=0)

    if grandmaster_side == 'white':
        browser.form['s[black_player]'] = ''
    else:
        browser.form['s[white_player]'] = ''

    response = browser.submit().read()
    soup = BeautifulSoup(response, 'html.parser')

    browser.close()

    opponent_full_name = get_full_player_name(analyzed_game['blackPlayer']) if grandmaster_side == 'white' \
        else get_full_player_name(analyzed_game['whitePlayer'])
    opponent_last_name = opponent_full_name.split(',')[0].split(' ')[0]

    white_player_rating = None
    black_player_rating = None

    for i in range(len(soup.select("td[class='black_elo rating']"))):
        game_opponent_name = soup.select("td[class='black_player name']")[i].text if grandmaster_side == 'white' \
            else soup.select("td[class='white_player name']")[i].text

        if opponent_last_name.lower() in game_opponent_name.lower():
            white_player_rating = soup.select("td[class='white_elo rating']")[i].text
            black_player_rating = soup.select("td[class='black_elo rating']")[i].text

            return white_player_rating, black_player_rating

    print('Could not detect elo ratings for game', analyzed_game)
    return white_player_rating or '-', black_player_rating or '-'


def contains_white_player_rating(analyzed_game):
    return 'whitePlayerRating' in analyzed_game \
           and analyzed_game['whitePlayerRating'] is not None \
           and len(analyzed_game['whitePlayerRating']) > 0


def contains_black_player_rating(analyzed_game):
    return 'blackPlayerRating' in analyzed_game \
           and analyzed_game['blackPlayerRating'] is not None \
           and len(analyzed_game['blackPlayerRating']) > 0


def get_database_player_name(incomplete_player_name):
    if incomplete_player_name in database_player_name_exceptions:
        return database_player_name_exceptions[incomplete_player_name]
    elif incomplete_player_name in player_name_cache:
        return player_name_cache[incomplete_player_name]
    else:
        return ''  # Unknown player

