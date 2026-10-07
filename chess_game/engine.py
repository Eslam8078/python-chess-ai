from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

Board = list[list[str]]
Square = tuple[int, int]

EMPTY = "  "
BOARD_SIZE = 8
PROMOTION_PIECES = ("Q", "R", "B", "N")

INITIAL_BOARD: Board = [
    ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
    ["bp"] * BOARD_SIZE,
    [EMPTY] * BOARD_SIZE,
    [EMPTY] * BOARD_SIZE,
    [EMPTY] * BOARD_SIZE,
    [EMPTY] * BOARD_SIZE,
    ["wp"] * BOARD_SIZE,
    ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"],
]

KNIGHT_OFFSETS = (
    (1, 2),
    (1, -2),
    (-1, 2),
    (-1, -2),
    (2, 1),
    (2, -1),
    (-2, 1),
    (-2, -1),
)
KING_OFFSETS = (
    (1, 1),
    (1, 0),
    (1, -1),
    (0, 1),
    (0, -1),
    (-1, 1),
    (-1, 0),
    (-1, -1),
)
DIAGONAL_DIRECTIONS = ((1, 1), (1, -1), (-1, 1), (-1, -1))
STRAIGHT_DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))


@dataclass(frozen=True, slots=True)
class Move:
    start: Square
    end: Square
    piece_moved: str
    piece_captured: str = EMPTY
    promotion_piece: Optional[str] = None
    is_en_passant: bool = False
    is_castle: bool = False

    @property
    def starting_row(self) -> int:
        return self.start[0]

    @property
    def starting_column(self) -> int:
        return self.start[1]

    @property
    def ending_row(self) -> int:
        return self.end[0]

    @property
    def ending_column(self) -> int:
        return self.end[1]

    @property
    def pawn_promotion(self) -> bool:
        return self.promotion_piece is not None

    @property
    def id(self) -> tuple:
        return self.start, self.end, self.promotion_piece, self.is_en_passant, self.is_castle

    def __str__(self) -> str:
        return f"{self._square_name(self.start)}-{self._square_name(self.end)}"

    @staticmethod
    def _square_name(square: Square) -> str:
        row, column = square
        return f"{chr(ord('a') + column)}{BOARD_SIZE - row}"


class GameState:
    def __init__(self) -> None:
        self.board: Board = [row[:] for row in INITIAL_BOARD]
        self.white_turn = True
        self.move_log: list[Move] = []
        self.white_king_location: Square = (7, 4)
        self.black_king_location: Square = (0, 4)
        self.en_passant_target: Optional[Square] = None
        self.castling_rights = {"K": True, "Q": True, "k": True, "q": True}
        self.check = False
        self._history: list[tuple[Board, bool, Square, Square, Optional[Square], dict[str, bool]]] = []

    @property
    def current_player(self) -> str:
        return "white" if self.white_turn else "black"

    def copy(self) -> GameState:
        state = GameState()
        state.board = [row[:] for row in self.board]
        state.white_turn = self.white_turn
        state.move_log = self.move_log[:]
        state.white_king_location = self.white_king_location
        state.black_king_location = self.black_king_location
        state.en_passant_target = self.en_passant_target
        state.castling_rights = self.castling_rights.copy()
        state.check = self.check
        return state

    def make_move(self, move: Move) -> None:
        self._history.append(
            (
                [row[:] for row in self.board],
                self.white_turn,
                self.white_king_location,
                self.black_king_location,
                self.en_passant_target,
                self.castling_rights.copy(),
            )
        )

        self.board[move.starting_row][move.starting_column] = EMPTY
        self.board[move.ending_row][move.ending_column] = move.piece_moved

        if move.is_en_passant:
            captured_row = move.ending_row + (1 if move.piece_moved[0] == "w" else -1)
            self.board[captured_row][move.ending_column] = EMPTY

        if move.pawn_promotion:
            promotion = move.promotion_piece or "Q"
            self.board[move.ending_row][move.ending_column] = move.piece_moved[0] + promotion

        if move.is_castle:
            self._move_castling_rook(move)

        self._update_king_location(move)
        self._update_castling_rights(move)
        self._update_en_passant_target(move)

        self.move_log.append(move)
        self.white_turn = not self.white_turn
        self.check = self.in_check(self.white_turn)

    def undo(self) -> Optional[Move]:
        if not self._history or not self.move_log:
            return None

        move = self.move_log.pop()
        board, white_turn, white_king, black_king, en_passant, rights = self._history.pop()
        self.board = board
        self.white_turn = white_turn
        self.white_king_location = white_king
        self.black_king_location = black_king
        self.en_passant_target = en_passant
        self.castling_rights = rights
        self.check = self.in_check(self.white_turn)
        return move

    def get_valid_moves(self) -> list[Move]:
        legal_moves: list[Move] = []
        moving_side = self.white_turn

        for move in self._get_pseudo_legal_moves():
            self.make_move(move)
            if not self.in_check(moving_side):
                legal_moves.append(move)
            self.undo()

        self.check = self.in_check(moving_side)
        return legal_moves

    def is_check_mate(self) -> bool:
        return self.in_check(self.white_turn) and not self.get_valid_moves()

    def is_stale_mate(self) -> bool:
        return not self.in_check(self.white_turn) and not self.get_valid_moves()

    def in_check(self, white: bool) -> bool:
        king = self.white_king_location if white else self.black_king_location
        return self.is_square_attacked(king, not white)

    def is_square_attacked(self, square: Square, by_white: bool) -> bool:
        row, column = square
        pawn_row = row + 1 if by_white else row - 1
        enemy_pawn = "wp" if by_white else "bp"
        if self._in_bounds(pawn_row, column - 1) and self.board[pawn_row][column - 1] == enemy_pawn:
            return True
        if self._in_bounds(pawn_row, column + 1) and self.board[pawn_row][column + 1] == enemy_pawn:
            return True

        attacker = "w" if by_white else "b"
        for row_offset, column_offset in KNIGHT_OFFSETS:
            target = (row + row_offset, column + column_offset)
            if self._in_bounds(*target) and self.board[target[0]][target[1]] == attacker + "N":
                return True

        for row_offset, column_offset in KING_OFFSETS:
            target = (row + row_offset, column + column_offset)
            if self._in_bounds(*target) and self.board[target[0]][target[1]] == attacker + "K":
                return True

        for row_offset, column_offset in DIAGONAL_DIRECTIONS:
            if self._ray_attacked(row, column, row_offset, column_offset, attacker, {"B", "Q"}):
                return True

        for row_offset, column_offset in STRAIGHT_DIRECTIONS:
            if self._ray_attacked(row, column, row_offset, column_offset, attacker, {"R", "Q"}):
                return True

        return False

    def _ray_attacked(
        self,
        row: int,
        column: int,
        row_offset: int,
        column_offset: int,
        attacker: str,
        piece_types: set[str],
    ) -> bool:
        current_row = row + row_offset
        current_column = column + column_offset
        while self._in_bounds(current_row, current_column):
            piece = self.board[current_row][current_column]
            if piece != EMPTY:
                return piece[0] == attacker and piece[1] in piece_types
            current_row += row_offset
            current_column += column_offset
        return False

    def _get_pseudo_legal_moves(self) -> list[Move]:
        moves: list[Move] = []
        color = "w" if self.white_turn else "b"

        for row in range(BOARD_SIZE):
            for column in range(BOARD_SIZE):
                piece = self.board[row][column]
                if piece == EMPTY or piece[0] != color:
                    continue

                if piece[1] == "p":
                    self._get_pawn_moves(row, column, moves)
                elif piece[1] == "N":
                    self._get_knight_moves(row, column, moves)
                elif piece[1] == "B":
                    self._get_sliding_moves(row, column, moves, DIAGONAL_DIRECTIONS)
                elif piece[1] == "R":
                    self._get_sliding_moves(row, column, moves, STRAIGHT_DIRECTIONS)
                elif piece[1] == "Q":
                    self._get_sliding_moves(row, column, moves, DIAGONAL_DIRECTIONS + STRAIGHT_DIRECTIONS)
                elif piece[1] == "K":
                    self._get_king_moves(row, column, moves)

        return moves

    def _get_pawn_moves(self, row: int, column: int, moves: list[Move]) -> None:
        color = "w" if self.white_turn else "b"
        enemy = "b" if self.white_turn else "w"
        direction = -1 if self.white_turn else 1
        start_row = 6 if self.white_turn else 1
        promotion_row = 0 if self.white_turn else 7
        one_step = row + direction

        if self._in_bounds(one_step, column) and self.board[one_step][column] == EMPTY:
            self._append_pawn_moves((row, column), (one_step, column), moves, promotion_row)
            two_step = row + 2 * direction
            if row == start_row and self.board[two_step][column] == EMPTY:
                moves.append(Move((row, column), (two_step, column), self.board[row][column]))

        for column_offset in (-1, 1):
            target = (one_step, column + column_offset)
            if not self._in_bounds(*target):
                continue
            target_piece = self.board[target[0]][target[1]]
            if target_piece != EMPTY and target_piece[0] == enemy and target_piece[1] != "K":
                self._append_pawn_moves((row, column), target, moves, promotion_row)
            elif target == self.en_passant_target:
                moves.append(
                    Move(
                        (row, column),
                        target,
                        self.board[row][column],
                        self.board[row][target[1]],
                        is_en_passant=True,
                    )
                )

    def _append_pawn_moves(
        self,
        start: Square,
        end: Square,
        moves: list[Move],
        promotion_row: int,
    ) -> None:
        if end[0] == promotion_row:
            for piece in PROMOTION_PIECES:
                moves.append(Move(start, end, self.board[start[0]][start[1]], self.board[end[0]][end[1]], piece))
        else:
            moves.append(Move(start, end, self.board[start[0]][start[1]], self.board[end[0]][end[1]]))

    def _get_knight_moves(self, row: int, column: int, moves: list[Move]) -> None:
        enemy = "b" if self.white_turn else "w"
        piece = self.board[row][column]
        for row_offset, column_offset in KNIGHT_OFFSETS:
            target = (row + row_offset, column + column_offset)
            if not self._in_bounds(*target):
                continue
            target_piece = self.board[target[0]][target[1]]
            if target_piece == EMPTY or (target_piece[0] == enemy and target_piece[1] != "K"):
                moves.append(Move((row, column), target, piece, target_piece))

    def _get_sliding_moves(
        self,
        row: int,
        column: int,
        moves: list[Move],
        directions: tuple[Square, ...],
    ) -> None:
        enemy = "b" if self.white_turn else "w"
        piece = self.board[row][column]
        for row_offset, column_offset in directions:
            for distance in range(1, BOARD_SIZE):
                target = (row + row_offset * distance, column + column_offset * distance)
                if not self._in_bounds(*target):
                    break
                target_piece = self.board[target[0]][target[1]]
                if target_piece == EMPTY:
                    moves.append(Move((row, column), target, piece))
                    continue
                if target_piece[0] == enemy and target_piece[1] != "K":
                    moves.append(Move((row, column), target, piece, target_piece))
                break

    def _get_king_moves(self, row: int, column: int, moves: list[Move]) -> None:
        enemy = "b" if self.white_turn else "w"
        piece = self.board[row][column]
        for row_offset, column_offset in KING_OFFSETS:
            target = (row + row_offset, column + column_offset)
            if not self._in_bounds(*target):
                continue
            target_piece = self.board[target[0]][target[1]]
            if target_piece == EMPTY or (target_piece[0] == enemy and target_piece[1] != "K"):
                moves.append(Move((row, column), target, piece, target_piece))

        self._get_castling_moves(row, column, moves)

    def _get_castling_moves(self, row: int, column: int, moves: list[Move]) -> None:
        color = "w" if self.white_turn else "b"
        home_row = 7 if self.white_turn else 0
        king_right = "K" if self.white_turn else "k"
        queen_right = "Q" if self.white_turn else "q"
        if (row, column) != (home_row, 4) or self.in_check(self.white_turn):
            return

        if self.castling_rights[king_right] and self._can_castle((home_row, 5), (home_row, 6), (home_row, 7)):
            moves.append(Move((home_row, 4), (home_row, 6), color + "K", is_castle=True))

        can_castle_queenside = self.castling_rights[queen_right] and self._can_castle(
            (home_row, 3), (home_row, 2), (home_row, 0), queenside=True
        )
        if can_castle_queenside:
            moves.append(Move((home_row, 4), (home_row, 2), color + "K", is_castle=True))

    def _can_castle(self, transit: Square, destination: Square, rook_square: Square, queenside: bool = False) -> bool:
        rook = "wR" if self.white_turn else "bR"
        if self.board[rook_square[0]][rook_square[1]] != rook:
            return False

        if queenside:
            empty_columns = (1, 2, 3)
        else:
            empty_columns = (5, 6)

        home_row = rook_square[0]
        if any(self.board[home_row][column] != EMPTY for column in empty_columns):
            return False

        return not self.is_square_attacked(transit, not self.white_turn) and not self.is_square_attacked(
            destination, not self.white_turn
        )

    def _move_castling_rook(self, move: Move) -> None:
        row = move.starting_row
        if move.ending_column == 6:
            rook_start, rook_end = (row, 7), (row, 5)
        else:
            rook_start, rook_end = (row, 0), (row, 3)
        self.board[rook_end[0]][rook_end[1]] = self.board[rook_start[0]][rook_start[1]]
        self.board[rook_start[0]][rook_start[1]] = EMPTY

    def _update_king_location(self, move: Move) -> None:
        if move.piece_moved == "wK":
            self.white_king_location = move.end
        elif move.piece_moved == "bK":
            self.black_king_location = move.end

    def _update_castling_rights(self, move: Move) -> None:
        if move.piece_moved == "wK":
            self.castling_rights["K"] = False
            self.castling_rights["Q"] = False
        elif move.piece_moved == "bK":
            self.castling_rights["k"] = False
            self.castling_rights["q"] = False

        rook_rights = {
            "wR": {(7, 0): "Q", (7, 7): "K"},
            "bR": {(0, 0): "q", (0, 7): "k"},
        }
        for square, right in rook_rights.get(move.piece_moved, {}).items():
            if move.start == square:
                self.castling_rights[right] = False

        if move.piece_captured in ("wR", "bR"):
            captured_rights = {
                (7, 0): "Q",
                (7, 7): "K",
                (0, 0): "q",
                (0, 7): "k",
            }
            right = captured_rights.get(move.end)
            if right:
                self.castling_rights[right] = False

    def _update_en_passant_target(self, move: Move) -> None:
        if move.piece_moved[1] == "p" and abs(move.starting_row - move.ending_row) == 2:
            self.en_passant_target = ((move.starting_row + move.ending_row) // 2, move.starting_column)
        else:
            self.en_passant_target = None

    @staticmethod
    def _in_bounds(row: int, column: int) -> bool:
        return 0 <= row < BOARD_SIZE and 0 <= column < BOARD_SIZE
