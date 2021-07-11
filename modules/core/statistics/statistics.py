import os
import chess.svg
import matplotlib.pyplot as plt
from modules.core.sides.sides import normalize_player_name, get_opponent_name


def save_good_move(grandmaster,
                   game_headers,
                   full_move_number,
                   turn,
                   move,
                   last_score,
                   new_score,
                   board_before_move,
                   board_after_move):

    output_directory = get_output_directory(grandmaster, game_headers)
    svg_base_file_name = output_directory \
                         + "/Move_" + str(full_move_number) + "_" \
                         + ("White" if turn == chess.WHITE else "Black") + "_" \
                         + move.uci()

    svg_before_file_name = svg_base_file_name + "/before_" + str(last_score) + "cp.svg"
    svg_after_file_name = svg_base_file_name + "/after_" + str(new_score) + "cp.svg"
    fen_before_file_name = svg_base_file_name + "/fen_before.txt"
    fen_after_file_name = svg_base_file_name + "/fen_after.txt"

    os.makedirs(svg_base_file_name, exist_ok=True)

    f = open(svg_before_file_name, "w")
    f.write(chess.svg.board(board_before_move))
    f.close()

    f = open(svg_after_file_name, "w")
    f.write(chess.svg.board(board_after_move, lastmove=move))
    f.close()

    f = open(fen_before_file_name, "w")
    f.write(board_before_move.fen())
    f.close()

    f = open(fen_after_file_name, "w")
    f.write(board_after_move.fen())
    f.close()


def plot_cp_scores(half_moves, cp_scores, grandmaster, grandmaster_side, game):
    output_directory = get_output_directory(grandmaster, game.headers)
    os.makedirs(output_directory, exist_ok=True)

    plt.title("CP Scores for " + game.headers["Site"] + " | " + game.headers["Date"])
    plt.xlabel("Half Move")
    plt.ylabel("CP Score")

    plt.xticks(range(min(half_moves), max(half_moves)+1, 4))

    plt.grid()

    opponent_name = normalize_player_name(get_opponent_name(grandmaster_side, game))

    color = "green" if grandmaster_side == chess.WHITE else "red"
    for i in range(len(half_moves) - 1):
        label = "" if i >= 2 else \
            ("Grandmaster " + grandmaster) if color == "green" else ("Opponent " + opponent_name)
        plt.plot(half_moves[i:i + 2], cp_scores[i:i + 2], color=color, label=label)
        color = "red" if color == "green" else "green"

    plt.legend(loc="upper left")
    plt.savefig(output_directory + "/cp_score_plot.png")
    # plt.show()

    plt.clf()
    plt.cla()
    plt.close()

    print("Saved cp scores plot as " + output_directory + "/cp_score_plot.png")


def plot_expectations(half_moves, expectations, grandmaster, grandmaster_side, game):
    output_directory = get_output_directory(grandmaster, game.headers)
    os.makedirs(output_directory, exist_ok=True)

    plt.title("Expectations for " + game.headers["Site"] + " | " + game.headers["Date"])
    plt.xlabel("Half Move")
    plt.ylabel("Expectation")

    plt.xticks(range(min(half_moves), max(half_moves)+1, 4))

    plt.grid()

    opponent_name = normalize_player_name(get_opponent_name(grandmaster_side, game))

    color = "green" if grandmaster_side == chess.WHITE else "red"
    for i in range(len(half_moves) - 1):
        label = "" if i >= 2 else \
            ("Grandmaster " + grandmaster) if color == "green" else ("Opponent " + opponent_name)
        plt.plot(half_moves[i:i + 2], expectations[i:i + 2], color=color, label=label)
        color = "red" if color == "green" else "green"

    plt.legend(loc="upper left")
    plt.savefig(output_directory + "/expectation_plot.png")
    # plt.show()

    plt.clf()
    plt.cla()
    plt.close()

    print("Saved expectations plot as " + output_directory + "/expectation_plot.png")


def get_output_directory(grandmaster, game_headers):
    return "output/" \
       + grandmaster + "/" \
       + game_headers["Event"].replace(" ", "_").replace("?", "X") \
       + "_" + game_headers["Site"].replace(" ", "_").replace("?", "X") \
       + "_" + game_headers["Date"].replace(" ", "_").replace(".", "-").replace("?", "X") \
       + "_" + game_headers["White"].replace(" ", "_") \
       + "_vs_" + game_headers["Black"].replace(" ", "_") \
       + "_" + game_headers["Round"] \
       + "_" + game_headers["Result"]
