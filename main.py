from __future__ import annotations

from pathlib import Path

import pygame

from chess_game import ChessAI, GameState, Move

BOARD_SIZE = 640
STATUS_HEIGHT = 64
WINDOW_WIDTH = BOARD_SIZE
WINDOW_HEIGHT = BOARD_SIZE + STATUS_HEIGHT
SQUARE_SIZE = BOARD_SIZE // 8
FPS = 60
AI_DEPTH = 3

LIGHT_SQUARE = pygame.Color(238, 218, 181)
DARK_SQUARE = pygame.Color(176, 121, 77)
SELECTED_SQUARE = pygame.Color(95, 158, 160)
MOVE_HINT = pygame.Color(55, 55, 55)
STATUS_BACKGROUND = pygame.Color(32, 35, 40)
STATUS_TEXT = pygame.Color(242, 242, 242)
PROMOTION_BACKGROUND = pygame.Color(245, 245, 245)
PROMOTION_TEXT = pygame.Color(32, 35, 40)

PIECE_NAMES = {
    "Q": "Queen",
    "R": "Rook",
    "B": "Bishop",
    "N": "Knight",
}


class ChessApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Python Chess")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 24)
        self.state = GameState()
        self.ai = ChessAI(AI_DEPTH)
        self.images: dict[str, pygame.Surface] = {}
        self.selected_square: tuple[int, int] | None = None
        self.valid_moves: list[Move] = self.state.get_valid_moves()
        self.move_made = False
        self.promotion_moves: list[Move] = []
        self.running = True
        self._load_images()

    def run(self) -> None:
        while self.running:
            self._handle_events()
            if self.running:
                self._play_ai_turn()
                self._update_state()
                self._draw()
                pygame.display.flip()
                self.clock.tick(FPS)
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._handle_key(event)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos)

    def _handle_key(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_ESCAPE:
            self.running = False
            return

        if event.key == pygame.K_r:
            self._reset_game()
            return

        if event.key == pygame.K_BACKSPACE and not self.promotion_moves:
            if self.state.move_log:
                self.state.undo()
                self.valid_moves = self.state.get_valid_moves()
                self.selected_square = None
                self.move_made = False
            return

        if self.promotion_moves:
            self._handle_promotion_key(event.key)

    def _handle_click(self, position: tuple[int, int]) -> None:
        if self.promotion_moves or self._game_over() or not self.state.white_turn:
            return

        column = position[0] // SQUARE_SIZE
        row = position[1] // SQUARE_SIZE
        if not (0 <= row < 8 and 0 <= column < 8):
            return

        if self.selected_square is None:
            self._select_square((row, column))
            return

        if self.selected_square == (row, column):
            self.selected_square = None
            return

        matching_moves = [
            move
            for move in self.valid_moves
            if move.start == self.selected_square and move.end == (row, column)
        ]

        if len(matching_moves) == 1:
            self.state.make_move(matching_moves[0])
            self.selected_square = None
            self.move_made = True
            return

        if len(matching_moves) > 1:
            self.promotion_moves = matching_moves
            return

        self._select_square((row, column))

    def _select_square(self, square: tuple[int, int]) -> None:
        piece = self.state.board[square[0]][square[1]]
        if piece != "  " and piece[0] == "w":
            if any(move.start == square for move in self.valid_moves):
                self.selected_square = square
                return
        self.selected_square = None

    def _handle_promotion_key(self, key: int) -> None:
        mapping = {
            pygame.K_q: "Q",
            pygame.K_r: "R",
            pygame.K_b: "B",
            pygame.K_n: "N",
        }
        promotion = mapping.get(key)
        if promotion is None:
            return
        selected = next((move for move in self.promotion_moves if move.promotion_piece == promotion), None)
        if selected is None:
            return
        self.state.make_move(selected)
        self.promotion_moves = []
        self.selected_square = None
        self.move_made = True

    def _play_ai_turn(self) -> None:
        if self.state.white_turn or self.promotion_moves or self._game_over():
            return
        move = self.ai.find_best_move(self.state, self.valid_moves)
        if move is None:
            return
        self.state.make_move(move)
        self.move_made = True

    def _update_state(self) -> None:
        if self.move_made:
            self.valid_moves = self.state.get_valid_moves()
            self.move_made = False

    def _reset_game(self) -> None:
        self.state = GameState()
        self.valid_moves = self.state.get_valid_moves()
        self.selected_square = None
        self.promotion_moves = []
        self.move_made = False

    def _game_over(self) -> bool:
        return self.state.is_check_mate() or self.state.is_stale_mate()

    def _draw(self) -> None:
        self._draw_board()
        self._draw_selection()
        self._draw_pieces()
        self._draw_status_bar()
        if self.promotion_moves:
            self._draw_promotion_overlay()

    def _draw_board(self) -> None:
        for row in range(8):
            for column in range(8):
                color = LIGHT_SQUARE if (row + column) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(
                    self.screen,
                    color,
                    pygame.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE),
                )

    def _draw_selection(self) -> None:
        if self.selected_square is None:
            return

        row, column = self.selected_square
        pygame.draw.rect(
            self.screen,
            SELECTED_SQUARE,
            pygame.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE),
            width=5,
        )

        destinations = [move.end for move in self.valid_moves if move.start == self.selected_square]
        overlay = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(overlay, (*MOVE_HINT, 115), (SQUARE_SIZE // 2, SQUARE_SIZE // 2), 9)
        for target_row, target_column in set(destinations):
            center = (target_column * SQUARE_SIZE + SQUARE_SIZE // 2, target_row * SQUARE_SIZE + SQUARE_SIZE // 2)
            self.screen.blit(overlay, (center[0] - SQUARE_SIZE // 2, center[1] - SQUARE_SIZE // 2))

    def _draw_pieces(self) -> None:
        for row in range(8):
            for column in range(8):
                piece = self.state.board[row][column]
                if piece != "  ":
                    self.screen.blit(
                        self.images[piece],
                        (column * SQUARE_SIZE, row * SQUARE_SIZE),
                    )

    def _draw_status_bar(self) -> None:
        area = pygame.Rect(0, BOARD_SIZE, WINDOW_WIDTH, STATUS_HEIGHT)
        pygame.draw.rect(self.screen, STATUS_BACKGROUND, area)
        status = self._status_text()
        text_surface = self.font.render(status, True, STATUS_TEXT)
        self.screen.blit(text_surface, (16, BOARD_SIZE + 17))
        controls = self.small_font.render("Backspace: Undo   R: Reset   Esc: Exit", True, STATUS_TEXT)
        self.screen.blit(controls, (WINDOW_WIDTH - controls.get_width() - 16, BOARD_SIZE + 20))

    def _status_text(self) -> str:
        if self.state.is_check_mate():
            winner = "Black" if self.state.white_turn else "White"
            return f"Checkmate — {winner} wins"
        if self.state.is_stale_mate():
            return "Stalemate — Draw"
        if self.promotion_moves:
            return "Promotion — press Q, R, B, or N"
        if self.state.in_check(self.state.white_turn):
            return f"{self.state.current_player.title()} is in check"
        return f"{self.state.current_player.title()} to move"

    def _draw_promotion_overlay(self) -> None:
        width = 420
        height = 170
        rect = pygame.Rect((WINDOW_WIDTH - width) // 2, (BOARD_SIZE - height) // 2, width, height)
        pygame.draw.rect(self.screen, PROMOTION_BACKGROUND, rect, border_radius=12)
        pygame.draw.rect(self.screen, DARK_SQUARE, rect, width=3, border_radius=12)

        title = self.font.render("Choose promotion piece", True, PROMOTION_TEXT)
        self.screen.blit(title, (rect.x + 24, rect.y + 24))

        options = "   ".join(f"{key}: {name}" for key, name in PIECE_NAMES.items())
        subtitle = self.small_font.render(options, True, PROMOTION_TEXT)
        self.screen.blit(subtitle, (rect.x + 24, rect.y + 78))

    def _load_images(self) -> None:
        assets = Path(__file__).resolve().parent / "assets" / "chess"
        for color in ("w", "b"):
            for piece_type in ("K", "Q", "R", "B", "N", "p"):
                key = color + piece_type
                image_path = assets / f"{key}.png"
                image = pygame.image.load(str(image_path)).convert_alpha()
                self.images[key] = pygame.transform.smoothscale(image, (SQUARE_SIZE, SQUARE_SIZE))


if __name__ == "__main__":
    ChessApp().run()
