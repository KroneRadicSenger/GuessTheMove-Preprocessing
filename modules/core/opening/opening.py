import glob
import io

import chess.pgn
import pandas as pd


ECO_FILES_DIRECTORY = "data/eco"


class OpeningECOReader:
    def __init__(self):
        self.eco_df = None

    def initialize(self):
        eco_files = glob.glob(ECO_FILES_DIRECTORY + "/*.tsv")
        eco_files_dataframes = []

        for eco_file in eco_files:
            df = pd.read_csv(eco_file, sep='\t', index_col=None, header=0)
            eco_files_dataframes.append(df)

        self.eco_df = pd.concat(eco_files_dataframes, axis=0, ignore_index=True)

    def identify_opening(self, pgn):
        game = chess.pgn.read_game(io.StringIO(pgn))
        board = game.board()

        opening = None

        while not game.is_end():
            move = game.variations[0].move
            game = game.variations[0]

            board.push(move)

            opening_detected = self.identify_opening_for_board(board)
            if opening_detected is not None:
                opening = opening_detected

        return opening

    def identify_opening_for_board(self, board):
        assert self.eco_df is not None, "dataframe should be initialized"

        openings_matched = self.eco_df.loc[self.eco_df['fen'] == board.epd()]
        return None if len(openings_matched) == 0 else openings_matched.iloc[0]
