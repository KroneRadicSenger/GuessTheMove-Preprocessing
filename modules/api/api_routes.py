import chess
import asyncio
from flask import Blueprint, request

from modules.core.engine.engine import initialize_uci_engine_sync, analyse_board_sync
from modules.core.evaluation.evaluation import evaluate_move_sync
from modules.core.score.score import get_signed_cp_score, get_expectation, get_current_score_for_grandmaster, \
    get_principle_variation, get_cp_score_string

api_routes = Blueprint('api routes', __name__, template_folder='templates')


result_cache = {}
analysis_cache = {}


@api_routes.route('/analyse')
def analyse():
    grandmaster_side_str = request.args.get('grandmasterSide')
    board_before_move_fen = request.args.get('boardBeforeMoveFen')
    board_after_move_fen = request.args.get('boardAfterMoveFen')
    last_opponent_move_was_blunder_str = request.args.get('lastOpponentMoveWasBlunder')
    move_played_san = request.args.get('movePlayedSan')

    if not grandmaster_side_str or not board_before_move_fen or not board_after_move_fen:
            return 'Missing url parameters', 400

    if (board_before_move_fen, board_after_move_fen) in result_cache:
        return result_cache[(board_before_move_fen, board_after_move_fen)]

    if not move_played_san or not last_opponent_move_was_blunder_str:
        return 'Missing url parameters', 400

    grandmaster_side = chess.WHITE if grandmaster_side_str.lower() == 'white' else chess.BLACK
    last_opponent_move_was_blunder = True if last_opponent_move_was_blunder_str.lower() == 'true' else False

    # Initialize UCI engine
    engine = initialize_uci_engine_sync()

    # Setup board before move
    board_before_move = chess.Board()
    board_before_move.set_fen(board_before_move_fen)

    # Parse turn and move played
    turn = 'white' if board_before_move.turn == chess.WHITE else 'black'
    move_played = board_before_move.parse_san(move_played_san)

    # Analyse board before move played
    if board_before_move_fen in analysis_cache:
        analysis_before_move = analysis_cache[board_before_move_fen]
    else:
        analysis_before_move = analyse_board_sync(engine, board_before_move, multipv=2, limit=chess.engine.Limit(depth=18))
        analysis_cache[board_before_move_fen] = analysis_before_move

    # Analyse score and expectation before move played
    score_before_move = get_signed_cp_score(analysis_before_move)
    gm_pov_score_before_move = get_current_score_for_grandmaster(score_before_move, grandmaster_side)
    expectation_before_move = get_expectation(gm_pov_score_before_move, board_before_move.ply())

    # Setup board after move
    board_after_move = chess.Board()
    board_after_move.set_fen(board_after_move_fen)

    # Analyse board after move played
    if board_after_move_fen in analysis_cache:
        analysis_after_move = analysis_cache[board_after_move_fen]
    else:
        analysis_after_move = analyse_board_sync(engine, board_after_move, multipv=2, limit=chess.engine.Limit(depth=18))
        analysis_cache[board_after_move_fen] = analysis_after_move

    # Analyse score and expectation after move played
    score_after_move = get_signed_cp_score(analysis_after_move)
    white_pov_score_after_move = get_current_score_for_grandmaster(score_after_move, chess.WHITE)
    gm_pov_score_after_move = get_current_score_for_grandmaster(score_after_move, grandmaster_side)
    expectation_after_move = get_expectation(gm_pov_score_after_move, board_after_move.ply())
    pv = [move_played] + get_principle_variation(analysis_after_move)

    # Analyse type of move played
    move_played_type, alternative_moves = \
         evaluate_move_sync(grandmaster_side, last_opponent_move_was_blunder, analysis_before_move,
                            board_before_move.ply(), move_played, expectation_before_move, expectation_after_move,
                            board_before_move, board_after_move)
    
    engine.quit()

    result = {
        "turn": turn,
        "evaluatedMove": {
            "move": {"uci": move_played.uci(), "san": board_before_move.san(move_played)},
            "moveType": move_played_type.value,
            "signedCPScore": get_cp_score_string(white_pov_score_after_move),
            "gmExpectation": expectation_after_move,
            "pv": board_before_move.variation_san(pv)
        },
        "alternativeMoves": alternative_moves
    }

    # Store result in cache
    result_cache[(board_before_move_fen, board_after_move_fen)] = result

    return result
