from chess_game import ChessAI
from chess_game.engine import EMPTY, GameState, Move


def test_initial_position_has_twenty_legal_moves() -> None:
    state = GameState()
    assert len(state.get_valid_moves()) == 20


def test_make_and_undo_restores_position() -> None:
    state = GameState()
    original = [row[:] for row in state.board]
    move = next(move for move in state.get_valid_moves() if str(move) == "e2-e4")

    state.make_move(move)
    assert state.board[4][4] == "wp"
    assert state.white_turn is False

    state.undo()
    assert state.board == original
    assert state.white_turn is True
    assert not state.move_log


def test_castling_is_generated_after_path_is_clear() -> None:
    state = GameState()
    state.board[7][5] = EMPTY
    state.board[7][6] = EMPTY
    state.board[6] = [EMPTY] * 8

    moves = state.get_valid_moves()
    assert any(move.is_castle and move.end == (7, 6) for move in moves)


def test_en_passant_is_generated_and_undoable() -> None:
    state = GameState()
    state.board = [[EMPTY] * 8 for _ in range(8)]
    state.board[3][4] = "wp"
    state.board[1][3] = "bp"
    state.board[7][4] = "wK"
    state.board[0][4] = "bK"
    state.white_king_location = (7, 4)
    state.black_king_location = (0, 4)
    state.white_turn = False

    black_move = Move((1, 3), (3, 3), "bp")
    state.make_move(black_move)

    move = next(move for move in state.get_valid_moves() if move.is_en_passant)
    state.make_move(move)
    assert state.board[2][3] == "wp"
    assert state.board[3][3] == EMPTY

    state.undo()
    assert state.board[3][3] == "bp"
    assert state.board[3][4] == "wp"


def test_promotion_generates_four_choices() -> None:
    state = GameState()
    state.board = [[EMPTY] * 8 for _ in range(8)]
    state.board[1][0] = "wp"
    state.board[7][4] = "wK"
    state.board[0][4] = "bK"
    state.white_king_location = (7, 4)
    state.black_king_location = (0, 4)

    moves = [move for move in state.get_valid_moves() if move.start == (1, 0) and move.end == (0, 0)]
    assert {move.promotion_piece for move in moves} == {"Q", "R", "B", "N"}


def test_ai_returns_a_legal_move() -> None:
    state = GameState()
    valid_moves = state.get_valid_moves()
    move = ChessAI(depth=1).find_best_move(state, valid_moves)
    assert move in valid_moves
