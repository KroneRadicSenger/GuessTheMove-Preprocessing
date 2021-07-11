import chess.gaviota

from modules.core.score.score import QUEEN_MATERIAL_VALUE, ROOK_MATERIAL_VALUE, get_material_value

GAVIOTA_FILE_PATH = "data/gaviota"

# The start of the endgame is not well defined. Therefore we use a common simple rule that says
# that a game is in endgame if both players have a material value less than the value of a Queen
# and a Rook combined or if the  game has a clear winning side.

ENDGAME_IF_MATERIAL_VALUE_IS_LESS_THAN = QUEEN_MATERIAL_VALUE + ROOK_MATERIAL_VALUE


def is_in_endgame(board, score, expectation):
    if score.is_mate() or expectation == 1:
        return True

    material_value_white = get_material_value(board, chess.WHITE)
    material_value_black = get_material_value(board, chess.BLACK)

    return material_value_white <= ENDGAME_IF_MATERIAL_VALUE_IS_LESS_THAN \
           and material_value_black <= ENDGAME_IF_MATERIAL_VALUE_IS_LESS_THAN


def get_gm_depth_to_mate(gm_side, board, last_score):
    sign = 1 if gm_side == board.turn else -1

    print()
    print("Trying to determine depth to mate using Gaviota tablebases.")

    # Gaviota endgame tablebases can tell us that the player to move mates in a certain amount of half moves
    with chess.gaviota.open_tablebase(GAVIOTA_FILE_PATH) as tablebase:
        gm_depth_to_mate = tablebase.get_dtm(board)

        if gm_depth_to_mate is None:
            print("Gaviota could not find a DTM for the last board in the game. Trying to get mate in with engine.")

            if last_score.is_mate():
                gm_depth_to_mate = last_score.relative.moves

        if gm_depth_to_mate is not None:
            gm_depth_to_mate = sign * gm_depth_to_mate
            print("Found Depth to Mate in Half Moves:", gm_depth_to_mate)

    return gm_depth_to_mate
