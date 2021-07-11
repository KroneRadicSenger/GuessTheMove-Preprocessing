import chess

ITERATIONS_TO_AVERAGE = 4

PAWN_MATERIAL_VALUE = 1
KNIGHT_MATERIAL_VALUE = 3
BISHOP_MATERIAL_VALUE = 3
ROOK_MATERIAL_VALUE = 5
QUEEN_MATERIAL_VALUE = 9


def get_current_score_for_grandmaster(signed_cp_score, grandmaster_side):
    return signed_cp_score.pov(grandmaster_side)


def get_pov_score(side, analysis, multipv_index=0):
    return get_signed_cp_score(analysis, multipv_index).pov(side)


def get_signed_cp_score(analysis, multipv_index=0):
    return analysis[multipv_index]["score"]


def get_principle_variation(analysis, multipv_index=0):
    try:
        return analysis[multipv_index]["pv"]
    except KeyError:
        # if there is no pv anymore (e.g. mate in zero)
        return []


def get_cp_score_string(signed_cp_score):
    if signed_cp_score.is_mate():
        return 'M{}'.format(signed_cp_score.mate())
    else:
        return '{0:+}'.format(signed_cp_score.score())


def get_expectation(pov_score, ply):
    return pov_score.wdl(ply=ply).expectation()


# not counting the king, get the current material value of the given side
def get_material_value(board, side):
    pawns = len(board.pieces(chess.PAWN, side))
    knights = len(board.pieces(chess.KNIGHT, side))
    bishops = len(board.pieces(chess.BISHOP, side))
    rooks = len(board.pieces(chess.ROOK, side))
    queens = len(board.pieces(chess.QUEEN, side))

    return pawns * PAWN_MATERIAL_VALUE + knights * KNIGHT_MATERIAL_VALUE + bishops * BISHOP_MATERIAL_VALUE + \
        rooks * ROOK_MATERIAL_VALUE + queens * QUEEN_MATERIAL_VALUE
