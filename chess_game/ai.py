from __future__ import annotations

from math import inf

from .engine import GameState, Move

CHECKMATE_SCORE = 100_000
PIECE_VALUES = {"p": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 20_000}


class ChessAI:
    def __init__(self, depth: int = 3) -> None:
        if depth < 1:
            raise ValueError("Search depth must be at least 1")
        self.depth = depth
        self.nodes_searched = 0

    def find_best_move(self, state: GameState, valid_moves: list[Move] | None = None) -> Move | None:
        moves = valid_moves if valid_moves is not None else state.get_valid_moves()
        if not moves:
            return None

        self.nodes_searched = 0
        ordered_moves = self._order_moves(moves)
        best_move = ordered_moves[0]
        best_score = -inf
        alpha = -inf
        beta = inf

        for move in ordered_moves:
            state.make_move(move)
            score = -self._search(state, self.depth - 1, -beta, -alpha, 1)
            state.undo()

            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)

        return best_move

    def _search(self, state: GameState, depth: int, alpha: float, beta: float, ply: int) -> float:
        self.nodes_searched += 1
        moves = state.get_valid_moves()
        if not moves:
            if state.in_check(state.white_turn):
                return -CHECKMATE_SCORE + ply
            return 0

        if depth == 0:
            score = self._evaluate(state)
            return score if state.white_turn else -score

        best_score = -inf
        for move in self._order_moves(moves):
            state.make_move(move)
            score = -self._search(state, depth - 1, -beta, -alpha, ply + 1)
            state.undo()

            best_score = max(best_score, score)
            alpha = max(alpha, score)
            if alpha >= beta:
                break

        return best_score

    def _evaluate(self, state: GameState) -> int:
        score = 0
        for row in state.board:
            for piece in row:
                if piece == "  ":
                    continue
                value = PIECE_VALUES[piece[1]]
                score += value if piece[0] == "w" else -value
        return score

    def _order_moves(self, moves: list[Move]) -> list[Move]:
        return sorted(moves, key=self._move_priority, reverse=True)

    @staticmethod
    def _move_priority(move: Move) -> int:
        capture_value = PIECE_VALUES.get(move.piece_captured[1], 0) if move.piece_captured != "  " else 0
        moving_value = PIECE_VALUES[move.piece_moved[1]]
        promotion_value = PIECE_VALUES.get(move.promotion_piece or "", 0)
        return capture_value * 10 - moving_value + promotion_value * 5 + (1_000 if move.is_castle else 0)
