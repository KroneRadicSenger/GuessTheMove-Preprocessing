from modules.core.sides.sides import did_grandmaster_win, normalize_player_name


def is_game_valid(grandmaster_name, game):
    if game is None:
        return False
    if game.errors:
        return False
    if game.board().uci_variant != "chess" \
            or not did_grandmaster_win(grandmaster_name, game):
        return False
    return True


def preprocess_game(game):
    game.headers["White"] = normalize_player_name(game.headers["White"])
    game.headers["Black"] = normalize_player_name(game.headers["Black"])
    game.headers["Date"] = game.headers["Date"].replace("??", "01")
