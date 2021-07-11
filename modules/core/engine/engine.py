import chess.engine

# Engine Options
ENGINE_PATH = "/usr/games/stockfish"

THREADS = 4
HASH_MEMORY = 2048
STOCKFISH_DEPTH = 18


async def initialize_uci_engine(use_nnue = False):
    _, engine = await chess.engine.popen_uci(ENGINE_PATH)
    await engine.configure({"Threads": THREADS, "Hash": HASH_MEMORY, "USE NNUE": use_nnue})
    return engine


def initialize_uci_engine_sync():
    return chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)


async def analyse_board(engine, board, multipv=3, limit=chess.engine.Limit(depth=STOCKFISH_DEPTH)):
    result = await engine.analyse(board, limit=limit, multipv=multipv)
    return result


def analyse_board_sync(engine, board, multipv=3, limit=chess.engine.Limit(depth=STOCKFISH_DEPTH)):
    return engine.analyse(board, limit=limit, multipv=multipv)
