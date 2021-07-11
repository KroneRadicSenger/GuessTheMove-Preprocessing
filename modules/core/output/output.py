import json
import uuid
from pathlib import Path
from datetime import datetime

import chess

class AnalyzedGame:
    def __init__(self, player_name, pgn, game, gm_side):
        self.id = str(uuid.uuid4())
        self.player_name = player_name
        self.pgn = pgn
        self.game = game
        self.white_player = self.game.headers["White"]
        self.black_player = self.game.headers["Black"]
        self.game_info = {
                    "event": self.game.headers["Event"],
                    "site": self.game.headers["Site"],
                    "date": self.game.headers["Date"],
                    "round": self.game.headers["Round"],
                }
        self.gm_side = gm_side
        self.gm_depth_to_mate = None
        self.opening = None
        self.moves = []

    def add_opening_move(self, ply, turn, evaluated_move):
        self.moves.append({
            "ply": ply,
            "gamePhase": "opening",
            "turn": "white" if turn == chess.WHITE else "black",
            "actualMove": evaluated_move,
            "alternativeMoves": []
        })
        # print(self.moves[len(self.moves) - 1])

    def add_move(self, ply, game_phase, turn, move_type, evaluated_move, alternative_moves):
        self.moves.append({
            "ply": ply,
            "gamePhase": game_phase,
            "turn": "white" if turn == chess.WHITE else "black",
            "actualMove": evaluated_move,
            "alternativeMoves": alternative_moves
        })
        # print(self.moves[len(self.moves) - 1])

    def set_opening(self, opening):
        self.opening = {
            "eco": opening["eco"],
            "name": opening["name"],
            "fen": opening["fen"],
            "moves": opening["moves"]
        }

    def set_gm_depth_to_mate(self, gm_depth_to_mate):
        self.gm_depth_to_mate = gm_depth_to_mate

    def save_as_json(self):
        output_dir = "output/" + self.player_name + "/splitted"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        full_filename = output_dir + "/" \
                        + self.white_player + "_vs_" \
                        + self.black_player + "_" \
                        + self.game_info["date"].replace("?", "X") + "_" \
                        + self.game_info["round"].replace("?", "X") \
                        + ".json"

        now = datetime.now()
        datetime_formatted = now.strftime("%d/%m/%Y %H:%M:%S")

        analysis_results = {
            "id": self.id,
            "addedDate": datetime_formatted,
            "pgn": self.pgn,
            "whitePlayer": self.white_player,
            "blackPlayer": self.black_player,
            "gameInfo": self.game_info,
            "gameAnalysis": {
                "grandmasterSide": "black" if self.gm_side == chess.BLACK else "white",
                "grandmasterDepthToMateInHalfMoves": self.gm_depth_to_mate,
                "opening": self.opening,
                "analyzedMoves": self.moves
            },
        }

        with open(full_filename, "w") as outfile:
            json.dump(analysis_results, outfile)

        print()
        print("Saved analysis output file at", full_filename)
        
        return analysis_results


def save_merged_analyzed_games_results(gm_name, merged_file_name, analyzed_games_results):
    output_dir = "output/" + gm_name
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    full_filename = output_dir + "/" \
                    + merged_file_name \
                    + ".json"

    with open(full_filename, "w") as outfile:
        json.dump(analyzed_games_results, outfile)

    print()
    print("Saved merged analysis output file at", full_filename)
