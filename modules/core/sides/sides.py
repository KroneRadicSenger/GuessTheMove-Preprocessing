import chess
from modules.core.constants.constants import Constants


def get_grandmaster_side(grandmaster, game):
    normalized_grandmaster_name = normalize_player_name(grandmaster)
    normalized_black_player_name = normalize_player_name(game.headers["Black"])

    return chess.BLACK if normalized_black_player_name == normalized_grandmaster_name else chess.WHITE


def get_grandmaster_name(grandmaster_side, game):
    return game.headers["White"] if grandmaster_side == chess.WHITE else game.headers["Black"]


def get_opponent_name(grandmaster_side, game):
    return game.headers["Black"] if grandmaster_side == chess.WHITE else game.headers["White"]


def normalize_player_name(player_name):
    if "," not in player_name:
        # TODO: for first or given names with more than one word, we can not
        #  distinguish between first name and last name
        splitted = player_name.split(" ")
        given_name = splitted[len(splitted) - 1]
        first_name = player_name[:-(len(given_name) + 1)]
    else:
        normalized_player_name = player_name.replace(", ", ",")
        if normalized_player_name.endswith("."):
            normalized_player_name = normalized_player_name[:-1]

        splitted = normalized_player_name.split(",")
        given_name = splitted[0]
        first_name = splitted[1]

        if len(first_name) == 1:
            pass

        if len(first_name) == 0:
            first_name = '?'

    return given_name + ", " + first_name


def is_grandmasters_turn(grandmaster, game, turn):
    return turn == get_grandmaster_side(grandmaster, game)


def get_winner_side(game):
    result = game.headers["Result"]
    if result == Constants.RESULT_DRAW:
        return None
    return chess.BLACK if result == Constants.RESULT_BLACK_WON else chess.WHITE


def did_grandmaster_win(grandmaster, game):
    return get_grandmaster_side(grandmaster, game) == get_winner_side(game)
