import os
import asyncio
import chess.pgn
import chess.engine
import click
import json
import pathlib
import gzip

from flask import Flask
from waitress import serve

from modules.api.api_routes import api_routes
from modules.core.endgame.endgame import is_in_endgame
from modules.core.engine.engine import initialize_uci_engine, analyse_board
from modules.core.opening.opening import OpeningECOReader
from modules.core.output.output import AnalyzedGame, save_merged_analyzed_games_results
from modules.core.pgn.pgn import is_game_valid, preprocess_game
from modules.core.sides.sides import get_grandmaster_side, is_grandmasters_turn, normalize_player_name
from modules.core.score.score import get_signed_cp_score, get_current_score_for_grandmaster, \
    get_expectation, get_cp_score_string, get_principle_variation
from modules.core.evaluation.evaluation import evaluate_move, MoveType
from modules.core.statistics.statistics import plot_cp_scores, plot_expectations
from modules.core.info.info import print_game_info
from modules.core.player.player import get_full_player_name, get_player_elo_ratings_for_game


@click.command()
@click.argument('grandmaster')
@click.argument('games', type=click.Path(exists=True))
@click.option('--statistics', is_flag=True)
def analyze(grandmaster, games, statistics):
    async def run_analysis():
        # Initialize UCI engine
        engine = await initialize_uci_engine()

        # Read game from pgn file
        pgn = open(games, "r")

        # Initialize opening reader
        opening_reader = OpeningECOReader()
        opening_reader.initialize()
        
        normalized_player_name = normalize_player_name(grandmaster)
        analyzed_games_results = []

        # Parse chess games from PGN file and process them to create game situations
        while True:
            # Check if game is valid for our purpose
            game = chess.pgn.read_game(pgn)
            if game is None:
                break
            if not is_game_valid(grandmaster, game):
                print("Game " + (str(game.headers) if game is not None else 'None') + " is invalid\n")
                continue

            # Game preprocessing
            preprocess_game(game)
            print_game_info(game, grandmaster)

            grandmaster_side = get_grandmaster_side(grandmaster, game)
            game_pgn = str(game)

            # Detect common opening played
            opening = opening_reader.identify_opening(game_pgn)
            if opening is None:
                print("Game opening could not be identified!\n")
                continue
            opening_ply_length = len(opening["moves"].split(" "))

            # Initialize analyzed game
            analyzed_game = AnalyzedGame(normalized_player_name, game_pgn, game, grandmaster_side)
            analyzed_game.set_opening(opening)

            # Initialize board
            node = game
            board = game.board()

            # Intiialize Game Phase data
            is_opening = True
            is_midgame = False
            is_endgame = False

            # Intiialize Analysis data
            score = None
            last_analysis = None
            last_expectation = 0.5
            last_opponent_move_was_blunder = False

            # Initialize Statistics data
            half_moves = [0]
            cp_scores = [0]
            expectations = [0.5]

            # Evaluate moves played by both players
            while not node.is_end():
                # Move data
                half_move = board.ply()
                # full_move = board.fullmove_number
                turn = board.turn
                move = node.variations[0].move
                # gm_turn = is_grandmasters_turn(grandmaster, game, turn)

                board_before_move = board.copy()

                # Play move of grandmaster
                board.push(move)

                # Update game phase
                if not is_midgame and half_move == opening_ply_length:
                    is_opening = False
                    is_midgame = True
                    print()
                    print("Begin of midgame!")

                # Analyse board after played Move
                analysis = await analyse_board(engine, board, multipv=3)
                score = get_signed_cp_score(analysis)
                white_pov_score = get_current_score_for_grandmaster(score, chess.WHITE)
                # white_expectation = get_expectation(white_pov_score, board.ply())
                gm_pov_score = get_current_score_for_grandmaster(score, grandmaster_side)
                expectation = get_expectation(gm_pov_score, board.ply())
                pv = [move] + get_principle_variation(analysis)

                # Update game phase
                if not is_endgame and is_in_endgame(board, score, expectation):
                    is_midgame = False
                    is_endgame = True
                    print()
                    print("Begin of endgame!")

                # Update statistics data
                half_moves += [half_move]
                cp_scores += [gm_pov_score.score()]
                expectations += [expectation]

                # print_move_info(full_move, half_move, turn, gm_turn, move, expectation, white_pov_score)
                # print(board_before_move.variation_san(pv))

                if is_opening:
                    # Add opening move played to analyzed game
                    analyzed_game.add_opening_move(ply=half_move, turn=turn, evaluated_move={
                                                       "move": {"uci": move.uci(), "san": board_before_move.san(move)},
                                                       "moveType": MoveType.BOOK.value,
                                                       "signedCPScore": get_cp_score_string(white_pov_score),
                                                       "gmExpectation": expectation,
                                                       "pv": board_before_move.variation_san(pv)
                                                   })
                else:
                    # Evaluate move played
                    move_type, alternative_moves = \
                        await evaluate_move(engine, grandmaster_side, last_opponent_move_was_blunder, last_analysis,
                                      half_move, move, last_expectation, expectation, board_before_move, board)

                    last_opponent_move_was_blunder = move_type == MoveType.BLUNDER
                    game_phase = "endgame" if is_endgame else "midgame"

                    # Add evaluated midgame/ endgame move to analyzed game
                    analyzed_game.add_move(ply=half_move, game_phase=game_phase, turn=board_before_move.turn, move_type=move_type.value,
                                           evaluated_move={
                                               "move": {"uci": move.uci(), "san": board_before_move.san(move)},
                                               "moveType": move_type.value,
                                               "signedCPScore": get_cp_score_string(white_pov_score),
                                               "gmExpectation": expectation,
                                               "pv": board_before_move.variation_san(pv)
                                           },
                                           alternative_moves=alternative_moves)

                last_analysis = analysis
                last_expectation = expectation
                node = node.variations[0]

            # TODO Remove comments to use endgame table base probing
            # gm_depth_to_mate = get_gm_depth_to_mate(grandmaster_side, board, score)
            # analyzed_game.set_gm_depth_to_mate(gm_depth_to_mate)

            # Add analyzed game result to total results list that will be saved as a json later
            analyzed_games_results.append(analyzed_game.save_as_json())

            # Save statistics if flag is set
            if statistics:
                plot_cp_scores(half_moves, cp_scores, normalized_player_name, grandmaster_side, game) 
                plot_expectations(half_moves, expectations, normalized_player_name, grandmaster_side, game)

        await engine.quit()
        
        input_file_name = click.format_filename(games).replace('\\', '/').split('/')[-1]
        merge_file_name = input_file_name.split('.')[0]
        save_merged_analyzed_games_results(normalized_player_name, merge_file_name, analyzed_games_results)

    asyncio.set_event_loop_policy(chess.engine.EventLoopPolicy())
    asyncio.run(run_analysis())


@click.command()
@click.argument('analysis', type=click.Path(exists=True))
@click.option('--output', '-o')
def annotate(analysis, output):
    print('Parsing input file..')

    # Read analysis output file created by 'analyze' command
    with open(analysis, "r") as analysis_output_file:
        analyzed_games_list = json.load(analysis_output_file)

        print('Annotating input file with full player names and elo ratings..')

        for analyzed_game in analyzed_games_list:
            white_player_full_name = get_full_player_name(analyzed_game['whitePlayer'])
            black_player_full_name = get_full_player_name(analyzed_game['blackPlayer'])
            white_player_rating, black_player_rating = get_player_elo_ratings_for_game(analyzed_game)

            analyzed_game['whitePlayer'] = white_player_full_name
            analyzed_game['blackPlayer'] = black_player_full_name
            analyzed_game['whitePlayerRating'] = white_player_rating
            analyzed_game['blackPlayerRating'] = black_player_rating

    print('Saving annotated output file..')

    # Prepare annotated file path
    output_file_path = output
    if output_file_path is None:
        output_dir = pathlib.Path(__file__).parent.absolute() / '..' / '..' / 'output' / 'annotated'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file_path = output_dir / os.path.basename(analysis_output_file.name)

    # Write annotated file
    with open(output_file_path, 'w') as annotated_output_file:
        json.dump(analyzed_games_list, annotated_output_file)

    print('Saved as', output_file_path)
    
    # Write gzipped annotated file that can be used as an analyzed games bundle for the app

    output_file_path_without_extension, _ = os.path.splitext(output_file_path)
    output_file_dir, output_file_name = os.path.split(output_file_path_without_extension)
    gzipped_output_file_path = os.path.join(output_file_dir, output_file_name + '_compressed')
    with open(output_file_path, 'rb') as file, gzip.open(gzipped_output_file_path, 'wb') as gzipped_file:
        gzipped_file.writelines(file)


@click.command()
@click.option('--debug', is_flag=True)
def api(debug):
    print('Starting Flask API..')
    
    app = Flask(__name__)
    app.register_blueprint(api_routes)
    
    if debug:
        app.run(debug=debug, threaded=True)
    else:
        # Use waitress for production server
        print('API running on port 5000')
        serve(app, host='0.0.0.0', port=5000)
