import chess
from modules.core.sides.sides import get_grandmaster_side


def print_game_info(game, grandmaster_name):
    grandmaster_side = get_grandmaster_side(grandmaster_name, game)
    game_length = game.end().board().fullmove_number
    opening = "unknown" if "ECO" not in game.headers else game.headers["ECO"]

    print("Game headers", game.headers)
    print("Opening", opening)
    print("Game Result", game.headers["Result"])
    print("Game length", game_length)
    print("Side of grandmaster", grandmaster_name, ":", "Black" if grandmaster_side == chess.BLACK else "White")
    print()
    print(game)


def print_move_info(full_move, half_move, turn, gm_turn, move, expectation, signed_cp_score):
    print()
    print("Ply " + str(half_move) + " (Full move " + str(full_move) + ")")
    print("Turn", "White" if turn == chess.WHITE else "Black", "(GM)" if gm_turn else "(Opponent)")
    print("Actual move:", move, "(Expectation:", expectation, ")")
    print("Signed CP Score:", signed_cp_score)


def print_full_move_info(full_move,
                         half_move,
                         turn,
                         gm_turn,
                         move,
                         last_score,
                         score,
                         last_expectation,
                         expectation):
    print("Full Move Number", full_move)
    print("Half Move Number", half_move)
    print("Turn", "White" if turn == chess.WHITE else "Black")
    print("Is GM turn:", gm_turn)
    print("Move", move)
    print("Is mate", score.is_mate())
    print("Last grandmaster score", last_score)
    print("New grandmaster score", score)
    print("Last grandmaster winning chance", last_expectation)
    print("New grandmaster winning chance", expectation)
    print("Difference", expectation - last_expectation)
