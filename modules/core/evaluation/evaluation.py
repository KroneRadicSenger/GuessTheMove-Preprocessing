from enum import Enum

import chess

from modules.core.score.score import get_pov_score, get_expectation, get_principle_variation, get_cp_score_string
from modules.core.engine.engine import analyse_board

ONLY_GOOD_MOVE_EPS = 0.10

BRILLIANT_MOVE_EXPECTATION_DELTA = 0.05
BEST_MOVE_EXPECTATION_DELTA = 0.05
EXCELLENT_MOVE_EXPECTATION_DELTA = 0.085
GOOD_MOVE_EXPECTATION_DELTA = 0.14

INACCURACY_MOVE_EXPECTATION_DELTA = 0.085
MISTAKE_MOVE_EXPECTATION_DELTA = 0.14
BLUNDER_MOVE_EXPECTATION_DELTA = 0.23

ALWAYS_FIND_BAD_SELECTION_MOVE_DEFAULT = True


class MoveType(Enum):
    BOOK = "book"
    BLUNDER = "blunder"
    MISTAKE = "mistake"
    INACCURACY = "inaccuracy"
    OKAY = "okay"
    GOOD = "good"
    EXCELLENT = "excellent"
    BEST = "best"
    BRILLIANT = "brilliant"
    CRITICAL = "critical"
    GAME_CHANGER = "gameChanger"


async def evaluate_move(engine, grandmaster_side, last_opponent_move_was_blunder, last_analysis,
                        half_move, move, last_expectation, new_expectation, board_before_move, board_after_move,
                        always_find_bad_selection_move=ALWAYS_FIND_BAD_SELECTION_MOVE_DEFAULT):
    best_next_moves, best_next_moves_cp_scores, best_next_moves_expectations, best_next_moves_pv \
        = find_best_next_moves(last_analysis, board_before_move.turn, half_move)

    gm_turn = board_before_move.turn == grandmaster_side

    move_type = evaluate_move_type(
        move, best_next_moves, best_next_moves_expectations, 
        last_expectation if gm_turn else (1 - last_expectation),  # get gm or opponents expectation
        new_expectation if gm_turn else (1 - new_expectation),  # get gm or opponents expectation,
        board_before_move, board_after_move, last_opponent_move_was_blunder
    )

    alternative_moves = await retrieve_alternative_moves(
        engine,
        best_next_moves, best_next_moves_cp_scores, best_next_moves_expectations, best_next_moves_pv, 
        move, move_type, board_before_move, 
        gm_turn,
        last_opponent_move_was_blunder,
        last_expectation if gm_turn else (1 - last_expectation),  # get gm or opponents old expectation
        always_find_bad_selection_move
    )
    
    return move_type, alternative_moves


def evaluate_move_sync(grandmaster_side, last_opponent_move_was_blunder, last_analysis,
                        half_move, move, last_expectation, new_expectation, board_before_move, board_after_move):
    best_next_moves, best_next_moves_cp_scores, best_next_moves_expectations, best_next_moves_pv \
        = find_best_next_moves(last_analysis, board_before_move.turn, half_move)

    gm_turn = board_before_move.turn == grandmaster_side

    move_type = evaluate_move_type(
        move, best_next_moves, best_next_moves_expectations, 
        last_expectation if gm_turn else (1 - last_expectation),  # get gm or opponents expectation
        new_expectation if gm_turn else (1 - new_expectation),  # get gm or opponents expectation,
        board_before_move, board_after_move, last_opponent_move_was_blunder
    )
    
    alternative_moves, _, _ = retrieve_alternative_moves_sync(
        best_next_moves, best_next_moves_cp_scores, best_next_moves_expectations, best_next_moves_pv, 
        move, board_before_move, 
        gm_turn,
        last_opponent_move_was_blunder,
        last_expectation if gm_turn else (1 - last_expectation),  # get gm or opponents old expectation
    )
    
    return move_type, alternative_moves


async def retrieve_alternative_moves(engine, best_next_moves, best_next_moves_cp_scores, best_next_moves_expectations,
                               best_next_moves_pv, actual_move, actual_move_type, board_before_move,
                               gm_turn, last_opponent_move_was_blunder, last_expectation,
                               always_find_bad_selection_move):
    alternative_moves, analyzed_alternative_moves, found_bad_alternative_move = retrieve_alternative_moves_sync(best_next_moves, best_next_moves_cp_scores, best_next_moves_expectations,
                               best_next_moves_pv, actual_move, board_before_move,
                               gm_turn, last_opponent_move_was_blunder, last_expectation)
    
    actual_move_is_bad = actual_move_type == MoveType.MISTAKE or actual_move_type == MoveType.INACCURACY or actual_move_type == MoveType.BLUNDER
    bad_move_found = found_bad_alternative_move or actual_move_is_bad

    # If the actual move and both alternative moves are at least good, try to replace the second alternative move
    # with a mistake or inaccuracy move if existing (or the best blunder found)
    # This ensures that, if possible, we never only have good moves to guess from
    if always_find_bad_selection_move and not bad_move_found and len(analyzed_alternative_moves) == 2:
        best_bad_move_turn_expectation = 0.0

        for legal_move in board_before_move.legal_moves:
            if actual_move == legal_move or legal_move in alternative_moves:
                continue
            
            board_after_legal_move = board_before_move.copy()
            board_after_legal_move.push(legal_move)
            
            legal_move_analysis = await analyse_board(engine, board_after_legal_move, multipv=1)

            legal_move_signed_cp_score = get_pov_score(chess.WHITE, legal_move_analysis)
            legal_move_turn_score = get_pov_score(board_before_move.turn, legal_move_analysis)
            legal_move_turn_expectation = get_expectation(legal_move_turn_score, board_before_move.ply())
            legal_move_pv = [legal_move] + get_principle_variation(legal_move_analysis)

            legal_move_type = evaluate_move_type(
                legal_move, best_next_moves, best_next_moves_expectations, 
                last_expectation, legal_move_turn_expectation,
                board_before_move, board_after_legal_move, 
                last_opponent_move_was_blunder
            )
            
            is_bad_move = legal_move_type == MoveType.MISTAKE or legal_move_type == MoveType.INACCURACY or legal_move_type == MoveType.BLUNDER
            
            analyzed_legal_move = {
                "move": {
                    "uci": legal_move.uci(),
                    "san": board_before_move.san(legal_move),
                },
                "moveType": legal_move_type.value,
                "signedCPScore": get_cp_score_string(legal_move_signed_cp_score),
                "gmExpectation": legal_move_turn_expectation if gm_turn else (1 - legal_move_turn_expectation),
                "pv": board_before_move.variation_san(legal_move_pv)
            }
            
            # Update alternative move if bad move with higher expectation was found
            if is_bad_move and legal_move_turn_expectation > best_bad_move_turn_expectation:
                analyzed_alternative_moves[1] = analyzed_legal_move
                best_bad_move_turn_expectation = legal_move_turn_expectation
            
            # Any inaccuracy or mistake is good enough for our bad move -> early stop
            if legal_move_type == MoveType.INACCURACY or legal_move_type == MoveType.MISTAKE:
                break
    
    return analyzed_alternative_moves


def retrieve_alternative_moves_sync(best_next_moves, best_next_moves_cp_scores, best_next_moves_expectations,
                               best_next_moves_pv, actual_move, board_before_move,
                               gm_turn, last_opponent_move_was_blunder, last_expectation):
    alternative_moves = []
    analyzed_alternative_moves = []
    found_bad_alternative_move = False

    # Use best next moves found as alternative moves
    # Note that although these are the best nest moves possible, they can include blunders, mistakes or inaccuracies if
    # there is only one good move (critical move)
    for i in range(len(best_next_moves)):
        # Only retrieve two alternative moves, not more
        if len(analyzed_alternative_moves) == 2:
            break
        
        alt_move = best_next_moves[i]
        if alt_move == actual_move:
            continue
    
        board_after_move = board_before_move.copy()
        board_after_move.push(alt_move)

        alt_move_type = evaluate_move_type(
            alt_move, best_next_moves, best_next_moves_expectations, 
            last_expectation, best_next_moves_expectations[i],
            board_before_move, board_after_move, 
            last_opponent_move_was_blunder
        )
        
        if alt_move_type == MoveType.BLUNDER or alt_move_type == MoveType.MISTAKE or alt_move_type == MoveType.INACCURACY:
            found_bad_alternative_move = True

        alternative_moves.append(alt_move)

        analyzed_alternative_moves.append(
            {
                "move": {
                    "uci": alt_move.uci(),
                    "san": board_before_move.san(alt_move),
                },
                "moveType": alt_move_type.value,
                "signedCPScore": get_cp_score_string(best_next_moves_cp_scores[i]),
                "gmExpectation": best_next_moves_expectations[i] if gm_turn else (1 - best_next_moves_expectations[i]),
                "pv": board_before_move.variation_san(best_next_moves_pv[i])
            })
    
    return alternative_moves, analyzed_alternative_moves, found_bad_alternative_move


def evaluate_move_type(move, best_next_moves, best_next_moves_expectations, last_expectation, new_expectation,
                       board_before_move, board_after_move, last_opponent_move_was_blunder):
    if played_critical_move(best_next_moves, best_next_moves_expectations, move,
                            new_expectation, board_before_move, board_after_move):
        return MoveType.CRITICAL
    elif played_brilliant_move(best_next_moves, move, best_next_moves_expectations[0], new_expectation):
        return MoveType.BRILLIANT
    elif played_best_move(best_next_moves, best_next_moves_expectations, move, new_expectation):
        if last_opponent_move_was_blunder:
            return MoveType.GAME_CHANGER
        else:
            return MoveType.BEST
    elif played_excellent_move(best_next_moves_expectations[0], new_expectation):
        return MoveType.EXCELLENT
    elif played_good_move(best_next_moves_expectations[0], new_expectation):
        return MoveType.GOOD
    elif played_blunder_move(last_expectation, new_expectation):
        return MoveType.BLUNDER
    elif played_mistake_move(last_expectation, new_expectation):
        return MoveType.MISTAKE
    elif played_inaccuracy_move(last_expectation, new_expectation):
        return MoveType.INACCURACY
    else:
        return MoveType.OKAY


def played_trivial_move(board_before_move, board_after_move, actual_move):
    # If grandmaster is in check before playing the move
    if board_before_move.is_check():
        return True

    # If the gradmaster move is a promotion (i.e. to Queen)
    if actual_move.promotion is not None:
        return True

    # If the game is over after the grandmaster move (e.g. if the move is a Mate-In-1)
    if board_after_move.is_game_over():
        return True

    return False


def played_inaccuracy_move(last_expectation, new_expectation):
    return (last_expectation - new_expectation) > INACCURACY_MOVE_EXPECTATION_DELTA


def played_mistake_move(last_expectation, new_expectation):
    return (last_expectation - new_expectation) > MISTAKE_MOVE_EXPECTATION_DELTA


def played_blunder_move(last_expectation, new_expectation):
    return (last_expectation - new_expectation) > BLUNDER_MOVE_EXPECTATION_DELTA


def played_good_move(best_next_move_expectation, actual_move_expectation):
    return abs(best_next_move_expectation - actual_move_expectation) <= GOOD_MOVE_EXPECTATION_DELTA


def played_excellent_move(best_next_move_expectation, actual_move_expectation):
    return abs(best_next_move_expectation - actual_move_expectation) <= EXCELLENT_MOVE_EXPECTATION_DELTA


def played_best_move(best_next_moves, best_next_moves_expectations, actual_move, actual_move_expectation):
    best_move_expectation = best_next_moves_expectations[0]

    i = 0
    expectation_diff_to_best_move = 0

    while actual_move != best_next_moves[i] \
            and expectation_diff_to_best_move <= BEST_MOVE_EXPECTATION_DELTA \
            and (i + 1) < len(best_next_moves):
        i += 1
        expectation_diff_to_best_move = best_move_expectation - best_next_moves_expectations[i]

    # Actual move is in list of best next moves and this move is actually close to the best move
    if actual_move == best_next_moves[i] and expectation_diff_to_best_move <= BEST_MOVE_EXPECTATION_DELTA:
        return True

    # Actual move is not in list of best next moves but equally as good
    return actual_move_expectation >= best_move_expectation \
        or (best_move_expectation - actual_move_expectation) <= BEST_MOVE_EXPECTATION_DELTA


def played_brilliant_move(best_next_moves, actual_move, best_next_move_expectation, actual_move_expectation):
    if actual_move in best_next_moves:
        return False

    if actual_move_expectation <= best_next_move_expectation:
        return False

    return actual_move_expectation - best_next_move_expectation >= BRILLIANT_MOVE_EXPECTATION_DELTA


def played_critical_move(best_next_moves, best_next_moves_expectations,
                         actual_move, actual_move_expectation, board_before_move, board_after_move):
    if played_trivial_move(board_before_move, board_after_move, actual_move):
        return False

    if not played_best_move(best_next_moves, best_next_moves_expectations, actual_move, actual_move_expectation):
        return False

    if len(best_next_moves_expectations) <= 1:
        return False

    best_move_expectation = best_next_moves_expectations[0]
    second_best_expectation = best_next_moves_expectations[1]

    if best_move_expectation <= second_best_expectation:
        return False

    return has_only_one_good_move(best_next_moves, best_next_moves_expectations)


def has_only_one_good_move(best_next_moves, best_next_moves_expectations):
    if len(best_next_moves) == 1:
        return True

    best_move_expectation = best_next_moves_expectations[0]
    second_best_move_expectation = best_next_moves_expectations[1]

    # Second best move is very bad and best move is quite good
    if second_best_move_expectation <= ONLY_GOOD_MOVE_EPS \
            and best_move_expectation >= 0.4:
        return True

    # Second best move is okay but best move is way better
    if second_best_move_expectation >= 0.35 \
            and best_move_expectation >= 1.5 * second_best_move_expectation:
        return True

    return False


def find_best_next_moves(last_analysis, turn, ply):
    best_next_moves = []
    best_next_moves_signed_cp_scores = []
    best_next_moves_expectations = []
    best_next_moves_pv = []

    for i in range(len(last_analysis)):
        i_best_move = get_best_move(last_analysis, i)

        i_signed_cp_score = get_pov_score(chess.WHITE, last_analysis, i)
        i_pov_score = get_pov_score(turn, last_analysis, i)
        i_winning_chance = get_expectation(i_pov_score, ply)
        i_pv = get_principle_variation(last_analysis, i)

        best_next_moves.append(i_best_move)
        best_next_moves_signed_cp_scores.append(i_signed_cp_score)
        best_next_moves_expectations.append(i_winning_chance)
        best_next_moves_pv.append(i_pv)

    return best_next_moves, best_next_moves_signed_cp_scores, best_next_moves_expectations, best_next_moves_pv


def get_best_move(analysis, multipv_index=0):
    return analysis[multipv_index]["pv"][0]
