from typing import Tuple, List
from enum import Enum
import time
import threading
import random
from gui import SantoriniGUI
from tkinter import Tk


class Level(Enum):
    """Represents the different building levels in Santorini."""

    GROUND = 0
    LEVEL1 = 1
    LEVEL2 = 2
    LEVEL3 = 3
    DOME = 4


class Tile:
    """Represents a tile on the game board."""

    def __init__(self):
        self.level = Level.GROUND
        self.worker = None

    def is_dome(self) -> bool:
        """Check if the tile has a dome."""
        return self.level == Level.DOME

    def is_higher_than(self, other_tile: "Tile") -> bool:
        """
        Check if this tile is at a higher level than another tile.

        Args:
            other_tile (Tile): The other tile to compare with.

        Returns:
            bool: True if this tile is higher, False otherwise.
        """
        return self.level.value > other_tile.level.value

    @property
    def level_value(self) -> int:
        """Get the numeric value of the current level."""
        return self.level.value

    def build(self) -> bool:
        """Build one level up on this tile."""
        if self.worker is not None or self.is_dome():
            return False

        if self.level == Level.LEVEL3:
            self.level = Level.DOME
        else:
            self.level = Level(self.level.value + 1)
        return True

    def __str__(self) -> str:
        """String representation of a tile."""
        if self.worker is not None:
            return f"{self.worker}{self.level.value}"
        elif self.is_dome():
            return "D"
        else:
            return str(self.level.value)


class Worker:
    """Represents a worker piece owned by a player."""

    def __init__(self, player, name):
        self.player = player
        self.name = name
        self.position = None
        self.prev_position = None

    def move_to(self, new_position: Tuple[int, int], board: "Board") -> bool:
        """
        Move the worker to a new position on the board.

        Args:
            new_position (Tuple[int, int]): The desired position to move to.
            board (Board): The game board instance.

        Returns:
            bool: True if the move is successful, False otherwise.
        """
        # Validate if the new position is valid
        if not board.is_valid_position(new_position):
            return False

        # Check if the target tile is occupied or has a dome
        target_tile = board.get_block(new_position)
        if target_tile.worker is not None or target_tile.is_dome():
            return False

        # Update the board: remove worker from the current position
        if self.position is not None:
            current_tile = board.get_block(self.position)
            current_tile.worker = None

        # Update the board: place worker at the new position
        target_tile.worker = self

        # Update the worker's position
        self.prev_position = self.position
        self.position = new_position
        return True

    def __str__(self) -> str:
        """String representation of a worker."""
        return self.name


class GodCard:
    """Base class for God cards that provide special abilities."""

    def __init__(self, name: str):
        self.name = name

    def can_use_power(self, worker, board, current_position) -> bool:
        """Check if the god power can be used in the current state."""
        return False

    def use_power(self, worker, board, target_position) -> bool:
        """Use the god power."""
        return False

    def __str__(self) -> str:
        return self.name


class Artemis(GodCard):
    """God card: Artemis - Your worker can move one additional time (but not back)."""

    def __init__(self):
        super().__init__("Artemis")

    def can_use_power(self, worker, board, current_position) -> bool:
        valid_moves = board.get_valid_moves(worker.position, False)
        if valid_moves and worker.prev_position in valid_moves:
            valid_moves.remove(worker.prev_position)
        return len(valid_moves) > 0


class Demeter(GodCard):
    """God card: Demeter - Your worker can build one additional time (but not on same space)."""

    def __init__(self):
        super().__init__("Demeter")

    def can_use_power(self, worker, board, current_position) -> bool:
        valid_builds = board.get_valid_builds(worker.position)
        return len(valid_builds) > 1


class Zeus(GodCard):
    """God card: Zeus - Your worker may build a block under itself."""

    def __init__(self):
        super().__init__("Zeus")

    def can_use_power(self, worker, board, current_position) -> bool:
        tile = board.get_block(worker.position)
        return tile and not tile.is_dome() and tile.level_value < 3


class Move:
    """Represents a worker movement action."""

    def __init__(
        self, worker: Worker, from_pos: Tuple[int, int], to_pos: Tuple[int, int]
    ):
        self.worker = worker
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.is_winning_move = False

    def execute(self, board: "Board") -> bool:
        """Execute the move on the board."""
        if not board.is_valid_position(self.to_pos):
            return False

        valid_moves = board.get_valid_moves(self.from_pos, False)
        if self.to_pos not in valid_moves:
            return False

        success = board.place_worker(self.worker, self.to_pos)

        if success:
            new_level = board.get_block(self.to_pos).level_value
            if new_level == Level.LEVEL3.value:
                self.is_winning_move = True

        return success

    def is_win(self) -> bool:
        """Check if this move resulted in a win."""
        return self.is_winning_move


class Build:
    """Represents a building action."""

    def __init__(self, position: Tuple[int, int], worker_pos: Tuple[int, int]):
        self.position = position
        self.worker_pos = worker_pos

    def execute(self, board: "Board") -> bool:
        """Execute the build on the board."""
        if not board.is_valid_position(self.position):
            return False

        valid_builds = board.get_valid_builds(self.worker_pos)
        if self.position not in valid_builds:
            return False

        tile = board.get_block(self.position)
        return tile.build()


class Board:
    """Represents the game board."""

    def __init__(self, size: int = 5):
        self.size = size
        self.grid = [[Tile() for _ in range(size)] for _ in range(size)]

    def is_valid_position(self, position: Tuple[int, int]) -> bool:
        """Check if a position is valid on the board."""
        row, col = position
        return 0 <= row < self.size and 0 <= col < self.size

    def get_block(self, position: Tuple[int, int]) -> Tile:
        """Get the tile at a specific position."""
        row, col = position
        if self.is_valid_position(position):
            return self.grid[row][col]
        return None

    def place_worker(self, worker: Worker, position: Tuple[int, int]) -> bool:
        """Place a worker at a position."""
        return worker.move_to(position, self)

    def get_adjacent_positions(
        self, position: Tuple[int, int]
    ) -> List[Tuple[int, int]]:
        """Get all valid adjacent positions (including diagonals)."""
        row, col = position
        adjacent = []
        for r in range(row - 1, row + 2):
            for c in range(col - 1, col + 2):
                if (r, c) != position and self.is_valid_position((r, c)):
                    adjacent.append((r, c))
        return adjacent

    def get_valid_moves(
        self, position: Tuple[int, int], athena_active: bool = False
    ) -> List[Tuple[int, int]]:
        """Get valid positions a worker can move to from a given position."""
        if not self.is_valid_position(position):
            return []

        current_block = self.get_block(position)
        current_level = current_block.level_value
        valid_moves = []

        for adj_pos in self.get_adjacent_positions(position):
            adj_block = self.get_block(adj_pos)
            if adj_block.worker is None and not adj_block.is_dome():
                adjacent_level = adj_block.level_value
                level_diff = adjacent_level - current_level

                if level_diff <= 1 and not (level_diff == 1 and athena_active):
                    valid_moves.append(adj_pos)

        return valid_moves

    def get_valid_builds(self, position: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get valid positions a worker can build on from a given position."""
        if not self.is_valid_position(position):
            return []

        valid_builds = []
        for adj_pos in self.get_adjacent_positions(position):
            adj_block = self.get_block(adj_pos)
            if adj_block.worker is None and not adj_block.is_dome():
                valid_builds.append(adj_pos)

        return valid_builds

    def get_valid_builds_with_zeus(self, position: tuple) -> list:
        """Get valid positions to build, including the worker's own position for Zeus."""
        valid_builds = self.get_valid_builds(position)

        tile = self.get_block(position)
        if tile and tile.worker and not tile.is_dome() and tile.level.value < 3:
            valid_builds.append(position)

        return valid_builds


class Player:
    """Represents a player in the game."""

    def __init__(self, name: str, god_card: GodCard = None, color: str = "#FFFFFF"):
        self.name = name
        self.god_card = god_card
        self.workers = [
            Worker(self, f"{name[0]}1"), Worker(self, f"{name[0]}2")]
        self.color = color
        self.dark_color = self._generate_darker_color(color)

    def _generate_darker_color(self, color: str) -> str:
        """Generate a darker shade of the given color."""
        if color.startswith("#"):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)

            r = int(r * 0.65)
            g = int(g * 0.65)
            b = int(b * 0.65)

            return f"#{r:02x}{g:02x}{b:02x}"
        return color

    def get_worker_positions(self) -> List[Tuple[int, int]]:
        """Get positions of both workers, filtering out None positions."""
        return [w.position for w in self.workers if w.position is not None]

    def __str__(self) -> str:
        """String representation of a player."""
        return self.name


class Timer:
    """A dedicated class to handle player timers for Santorini."""

    def __init__(self, game, minutes_per_player=15):
        """Initialize the timer with a reference to the game and minutes per player."""
        self.game = game
        self.enabled = True
        # Store time in seconds for each player
        self.player_timers = [minutes_per_player *
                              60 for _ in range(len(game.players))]
        self.running = False
        self.thread = None
        self.current_timer_start = None

    def start(self):
        """Start the timer for the current player."""
        if not self.enabled or self.running:
            return

        self.running = True
        self.current_timer_start = time.time()

        def timer_tick():
            while self.running:
                time.sleep(0.1)
                if self.current_timer_start is not None:
                    elapsed = time.time() - self.current_timer_start
                    self.player_timers[self.game.current_player_index] -= elapsed
                    self.current_timer_start = time.time()

                    # Check if time ran out
                    if self.player_timers[self.game.current_player_index] <= 0:
                        self.player_timers[self.game.current_player_index] = 0
                        self.running = False

                        if self.game.gui:
                            self.game.gui.root.after(0, self.handle_timeout)

                    # Update timer display continuously
                    if self.game.gui:
                        self.game.gui.root.after(
                            0, self.game.gui.update_timer_display)

        self.thread = threading.Thread(target=timer_tick, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the current player's timer."""
        if self.running and self.current_timer_start is not None:
            elapsed = time.time() - self.current_timer_start
            self.player_timers[self.game.current_player_index] -= elapsed
            self.current_timer_start = None

        self.running = False

    def get_display(self, player_index):
        """Get the formatted time display for a player."""
        seconds = max(0, int(self.player_timers[player_index]))
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def handle_timeout(self):
        """Handle a player running out of time."""
        if self.game.winner is None:
            # Current player loses, other player wins
            current_player = self.game.current_player_index
            winner_index = (current_player + 1) % len(self.game.players)
            self.game.winner = self.game.players[winner_index]

            if self.game.gui:
                current_player_name = self.game.get_current_player().name
                self.game.gui.update_status_text(
                    f"Time's up! {current_player_name} loses!")
                self.game.gui.show_game_over(f"{self.game.winner.name} wins!")


class Hint:
    """A simple class to provide strategic hints for the current player."""

    @staticmethod
    def find_best_move(game):
        """Find a good move for the current player based on simple heuristics."""
        current_player = game.get_current_player()
        best_score = -1
        best_action = None

        # Find best move based on game phase
        if game.phase == "select":
            # Evaluate each worker
            for worker in current_player.workers:
                if not worker.position:
                    continue

                valid_moves = game.board.get_valid_moves(
                    worker.position, game.athena_activated)
                if valid_moves:
                    # Simply choose the worker with most valid moves
                    if len(valid_moves) > best_score:
                        best_score = len(valid_moves)
                        best_action = {
                            "type": "select",
                            "worker": worker,
                            "position": worker.position
                        }

        elif game.phase == "move" and game.selected_worker:
            # Find best move for selected worker
            valid_moves = game.board.get_valid_moves(
                game.selected_worker.position, game.athena_activated)

            for move_pos in valid_moves:
                score = 0
                # Get levels
                current_level = game.board.get_block(
                    game.selected_worker.position).level_value
                target_level = game.board.get_block(
                    move_pos).level_value
                # Prioritize moving up
                if target_level > current_level:
                    score += 5 * (target_level - current_level)

                # Prioritize level 3 (winning move)
                if target_level == 3:
                    score += 100

                if score > best_score:
                    best_score = score
                    best_action = {
                        "type": "move",
                        "position": move_pos
                    }

        elif game.phase == "build" and game.selected_worker:
            # Find best build
            valid_builds = game.board.get_valid_builds(
                game.selected_worker.position)

            for build_pos in valid_builds:
                # Changed from get_level_value()
                build_level = game.board.get_block(build_pos).level_value
                score = 0

                # Prefer builds that reach higher levels
                score = 3 - build_level  # Prioritize building to level 3

                if score > best_score:
                    best_score = score
                    best_action = {
                        "type": "build",
                        "position": build_pos
                    }

        return best_action


class Game:
    """Main class for the Santorini game."""

    def __init__(self, gui=None):
        self.board = Board()
        self.players = []
        self.current_player_index = 0
        self.winner = None
        self.turn_count = 0
        self.start_time = None
        self.athena_activated = False
        self.last_move_data = None
        self.game_history = []
        self.game_mode = "Classic"
        self.gui = gui
        self.selected_worker = None
        self.phase = "setup"
        self.second_action = None
        self.god_power_active = False
        self.last_move = None
        self.last_build = None
        self.timer = None
        self.hint_counts = [3, 3]  # 3 hints per player

    def randomly_place_workers(self):
        """Randomly place all workers on the board at the start of the game."""
        available_positions = [
            (r, c) for r in range(self.board.size) for c in range(self.board.size)
        ]
        random.shuffle(available_positions)

        for player in self.players:
            for worker in player.workers:
                if available_positions:
                    position = available_positions.pop()
                    self.board.place_worker(worker, position)
                    if self.gui:
                        self.gui.update_board()

    def next_turn(self):
        """Advance to the next player's turn."""
        self.stop_timer()

        self.current_player_index = (
            self.current_player_index + 1) % len(self.players)
        self.turn_count += 1
        self.selected_worker = None
        self.phase = "select"
        self.second_action = None
        self.god_power_active = False

        if self.check_game_over():
            return

        # Update hint button state for the new player
        if self.gui and hasattr(self.gui, 'hint_button'):
            # Enable/disable hint button based on current player's hint count
            if self.hint_counts[self.current_player_index] > 0:
                self.gui.hint_button.config(state="normal")
            else:
                self.gui.hint_button.config(state="disabled")

        if self.gui:
            self.gui.update_status_text(
                f"{self.get_current_player().name}'s turn. Select a worker."
            )
            self.gui.update_turn_indicator()
            self.gui.update_timer_display()

        self.start_timer()

    def _handle_select_phase(self, position):
        """Select a worker to move."""
        current_player = self.get_current_player()
        tile = self.board.get_block(position)

        if tile and tile.worker:
            worker = tile.worker

            if worker.player != current_player:
                if self.gui:
                    self.gui.update_status_text(
                        f"That's {worker.player.name}'s worker. Select your own worker."
                    )
                return

            valid_moves = self.board.get_valid_moves(
                position, self.athena_activated)

            if valid_moves:
                self.selected_worker = worker
                self.phase = "move"
                if self.gui:
                    self.gui.update_status_text(
                        f"Selected {worker.name}. Choose where to move."
                    )
                    self.gui.highlight_tiles(valid_moves)
            else:
                if self.gui:
                    self.gui.update_status_text(
                        f"Worker {worker.name} has no valid moves."
                    )
        else:
            if self.gui:
                self.gui.update_status_text("Select your worker.")

    def add_player(
        self, name: str, god_card: GodCard = None, color: str = "#FFFFFF"
    ) -> Player:
        """Add a new player to the game."""
        player = Player(name, god_card, color)
        self.players.append(player)
        return player

    def handle_tile_click(self, row, col):
        """Handle player interaction with a board tile based on current game phase."""
        if self.winner:
            return

        position = (row, col)

        if self.phase == "place":
            self._handle_place_phase(position)
        elif self.phase == "select":
            self._handle_select_phase(position)
        elif self.phase == "move":
            self._handle_move_phase(position)
        elif self.phase == "build":
            self._handle_build_phase(position)
        elif self.phase == "second_move":
            self._handle_second_move_phase(position)
        elif self.phase == "second_build":
            self._handle_second_build_phase(position)

    def _handle_build_phase(self, position):
        """Build with selected worker."""
        if not self.selected_worker:
            return

        current_player = self.get_current_player()
        is_zeus = (self.god_power_active and
                   current_player.god_card and
                   current_player.god_card.name == "Zeus")

        if is_zeus:
            valid_builds = self.board.get_valid_builds_with_zeus(
                self.selected_worker.position)
        else:
            valid_builds = self.board.get_valid_builds(
                self.selected_worker.position)

        if position in valid_builds:
            # If building under the worker (Zeus power)
            if position == self.selected_worker.position:
                tile = self.board.get_block(position)
                if tile and not tile.is_dome() and tile.level_value < 3:
                    # Temporarily remove worker to build
                    worker = tile.worker
                    tile.worker = None

                    # Build on the tile
                    tile.build()

                    # Put worker back
                    tile.worker = worker

                    if self.gui:
                        self.gui.update_board()
                        self.gui.clear_highlights()

                    self.next_turn()
                    return
            else:
                # Normal build
                build = Build(position, self.selected_worker.position)
                if build.execute(self.board):
                    self.last_build = build

                    player = self.selected_worker.player
                    if (
                        player.god_card
                        and player.god_card.name == "Demeter"
                        and self.god_power_active
                        and any(pos != position for pos in valid_builds)
                    ):
                        valid_second_builds = [
                            pos for pos in valid_builds if pos != position
                        ]
                        if valid_second_builds:
                            self.phase = "second_build"
                            self.second_action = {
                                "type": "build", "first_pos": position}
                            if self.gui:
                                self.gui.update_board()
                                self.gui.update_status_text(
                                    "Demeter power: Build again (not same space). Select position or skip."
                                )
                                self.gui.highlight_tiles(
                                    valid_second_builds, "#ADD8E6")
                                self.gui.show_skip_button()
                            return

                    if self.gui:
                        self.gui.update_board()
                        self.gui.clear_highlights()
                    self.next_turn()
        else:
            if self.gui:
                self.gui.update_status_text(
                    "Invalid build. Choose highlighted position."
                )

    def get_current_player(self) -> Player:
        """Get the current player whose turn it is."""
        return self.players[self.current_player_index]

    def _handle_place_phase(self, position):
        """Place workers on the board."""
        current_player = self.get_current_player()

        worker_to_place = next(
            (w for w in current_player.workers if w.position is None), None
        )

        if worker_to_place:
            if self.board.place_worker(worker_to_place, position):
                if self.gui:
                    self.gui.update_board()
                    self.gui.update_status_text(
                        f"Placed {worker_to_place.name} at {position}"
                    )

                all_current_player_workers_placed = all(
                    w.position is not None for w in current_player.workers
                )

                if all_current_player_workers_placed:
                    self.current_player_index = (self.current_player_index + 1) % len(
                        self.players
                    )
                    current_player = self.get_current_player()

                    all_placed = all(
                        all(w.position is not None for w in p.workers)
                        for p in self.players
                    )
                    if all_placed:
                        self.phase = "select"
                        self.turn_count += 1
                        self.selected_worker = None
                        self.second_action = None
                        if self.gui:
                            self.gui.update_status_text(
                                f"{current_player.name}'s turn. Select a worker."
                            )
                            self.gui.update_turn_indicator()
                    else:
                        if self.gui:
                            self.gui.update_status_text(
                                f"{current_player.name}, place your workers."
                            )
                            self.gui.update_turn_indicator()
                else:
                    if self.gui:
                        self.gui.update_status_text(
                            f"{current_player.name}, place your next worker."
                        )
            else:
                if self.gui:
                    self.gui.update_status_text(
                        "Cannot place worker here. Position occupied."
                    )
        else:
            self.next_turn()

    def activate_god_power(self) -> bool:
        """
        Activate the god power for the current player's turn.
        Returns True if the god power was activated, False otherwise.
        """
        current_player = self.get_current_player()

        if not current_player.god_card:
            if self.gui:
                self.gui.update_status_text(
                    f"{current_player.name} doesn't have a god card."
                )
            return False

        valid_phases = ["select", "move", "build"]
        if self.phase not in valid_phases:
            if self.gui:
                self.gui.update_status_text(
                    "Cannot use god power during this phase.")
            return False

        if self.god_power_active:
            if self.gui:
                self.gui.update_status_text(
                    "God power already activated for this turn."
                )
            return False

        self.god_power_active = True

        if self.gui:
            self.gui.update_status_text(
                f"{current_player.god_card.name} power activated!"
            )

        return True

    def start_game(self):
        """Start the game and initialize the timer."""
        self.start_time = time.time()

        self.randomly_place_workers()

        # Initialize timers for both players
        self.initialize_timers(15)  # 15 minutes per player

        self.phase = "select"
        if self.gui:
            self.gui.update_status_text(
                f"Game started! Each player has 3 hints for the entire game."
            )
            # After a short delay, show the normal start message
            self.gui.root.after(2000, lambda: self.gui.update_status_text(
                f"{self.get_current_player().name}'s turn. Select a worker."
            ))
            self.gui.update_turn_indicator()
            self.gui.update_timer_display()

            self.gui.update_turn_indicator()
            self.gui.update_timer_display()

        self.start_timer()

    def _handle_move_phase(self, position):
        """Move selected worker to new position."""
        if not self.selected_worker:
            return

        valid_moves = self.board.get_valid_moves(
            self.selected_worker.position, self.athena_activated
        )

        if position in valid_moves:
            worker = self.selected_worker
            prev_position = worker.position
            prev_level = self.board.get_block(prev_position).level_value

            move = Move(worker, prev_position, position)
            if move.execute(self.board):
                self.last_move = move

                if move.is_win():
                    self.winner = worker.player
                    if self.gui:
                        self.gui.update_board()
                        self.gui.update_status_text(
                            f"{worker.player.name} wins by reaching level 3!"
                        )
                        self.gui.show_game_over(f"{worker.player.name} wins!")
                    return

                player = worker.player
                if (
                    player.god_card
                    and player.god_card.name == "Artemis"
                    and self.god_power_active
                ):
                    if player.god_card.can_use_power(worker, self.board, position):
                        valid_second_moves = self.board.get_valid_moves(
                            position, self.athena_activated
                        )
                        if prev_position in valid_second_moves:
                            valid_second_moves.remove(prev_position)

                        if valid_second_moves:
                            self.phase = "second_move"
                            self.second_action = {
                                "type": "move", "first_pos": position}
                            if self.gui:
                                self.gui.update_board()
                                self.gui.update_status_text(
                                    "Artemis power: You can move again (not back). Select position or skip."
                                )
                                self.gui.highlight_tiles(valid_second_moves)
                                self.gui.show_skip_button()
                            return

                self.phase = "build"
                valid_builds = self.board.get_valid_builds(position)
                if self.gui:
                    self.gui.update_board()
                    self.gui.update_status_text("Select position to build.")
                    self.gui.highlight_tiles(valid_builds, "#ADD8E6")
        else:
            if self.gui:
                self.gui.update_status_text(
                    "Invalid move. Choose highlighted position."
                )

    def _handle_second_move_phase(self, position):
        """Handle Artemis' second move."""
        if (
            not self.selected_worker
            or not self.second_action
            or self.second_action["type"] != "move"
        ):
            return

        first_pos = self.second_action["first_pos"]
        valid_moves = self.board.get_valid_moves(
            self.selected_worker.position, self.athena_activated
        )

        if self.selected_worker.prev_position in valid_moves:
            valid_moves.remove(self.selected_worker.prev_position)

        if position in valid_moves:
            worker = self.selected_worker
            prev_position = worker.position

            move = Move(worker, prev_position, position)
            if move.execute(self.board):
                if move.is_win():
                    self.winner = worker.player
                    if self.gui:
                        self.gui.update_board()
                        self.gui.hide_skip_button()
                        self.gui.update_status_text(
                            f"{worker.player.name} wins by reaching level 3!"
                        )
                        self.gui.show_game_over(f"{worker.player.name} wins!")
                    return

                self.phase = "build"
                valid_builds = self.board.get_valid_builds(position)
                if self.gui:
                    self.gui.update_board()
                    self.gui.hide_skip_button()
                    self.gui.update_status_text("Select position to build.")
                    self.gui.highlight_tiles(valid_builds, "#ADD8E6")
        else:
            if self.gui:
                self.gui.update_status_text(
                    "Invalid build location. Choose highlighted position."
                )

    def _handle_second_build_phase(self, position):
        """Handle Demeter's second build."""
        if (
            not self.selected_worker
            or not self.second_action
            or self.second_action["type"] != "build"
        ):
            return

        first_build_pos = self.second_action["first_pos"]
        valid_builds = [
            pos
            for pos in self.board.get_valid_builds(self.selected_worker.position)
            if pos != first_build_pos
        ]

        if position in valid_builds:
            build = Build(position, self.selected_worker.position)
            if build.execute(self.board):
                if self.gui:
                    self.gui.update_board()
                    self.gui.hide_skip_button()
                    self.gui.clear_highlights()
                self.next_turn()
        else:
            if self.gui:
                self.gui.update_status_text(
                    "Invalid second build. Choose highlighted position."
                )

    def skip_second_action(self):
        """Skip the second action (move or build) from god power."""
        if self.phase == "second_move":
            self.phase = "build"
            valid_builds = self.board.get_valid_builds(
                self.selected_worker.position)
            if self.gui:
                self.gui.hide_skip_button()
                self.gui.update_status_text("Select position to build.")
                self.gui.highlight_tiles(valid_builds, "#ADD8E6")

        elif self.phase == "second_build":
            if self.gui:
                self.gui.hide_skip_button()
                self.gui.clear_highlights()
            self.next_turn()

    def check_game_over(self):
        """Check if current player has any valid moves."""
        if self.phase != "select" or self.winner:
            return False

        current_player = self.get_current_player()
        can_move = False

        for worker in current_player.workers:
            if worker.position and self.board.get_valid_moves(
                worker.position, self.athena_activated
            ):
                can_move = True
                break

        if not can_move:
            self.winner = self.players[
                (self.current_player_index + 1) % len(self.players)
            ]
            if self.gui:
                self.gui.update_status_text(
                    f"{current_player.name} has no valid moves!"
                )
                self.gui.show_game_over(f"{self.winner.name} wins!")
            return True

    def initialize_timers(self, minutes_per_player=15):
        """Initialize game timers for each player."""
        self.timer = Timer(self, minutes_per_player)

    def start_timer(self):
        """Start the timer for the current player."""
        if self.timer:
            self.timer.start()

    def stop_timer(self):
        """Stop the current player timer."""
        if self.timer:
            self.timer.stop()

    def get_timer_display(self, player_index):
        """Get the time display for a player."""
        if self.timer:
            return self.timer.get_display(player_index)
        return "00:00"

    def handle_timeout(self):
        """Handle player running out of time."""
        if self.winner is None:
            # Current player loses, other player wins
            self.winner = self.players[(
                self.current_player_index + 1) % len(self.players)]
            if self.gui:
                self.gui.update_status_text(
                    f"Time's up! {self.get_current_player().name} loses!")
                self.gui.show_game_over(f"{self.winner.name} wins!")

    def provide_hint(self):
        """Provide a hint for the current player."""
        if self.winner:
            return None

        # Check if player has hints remaining
        player_index = self.current_player_index
        if not hasattr(self, 'hint_counts'):
            self.hint_counts = [3, 3]  # Initialize if not already done

        if self.hint_counts[player_index] <= 0:
            if self.gui:
                self.gui.update_status_text(
                    f"All hints for {self.get_current_player().name} have been used!"
                )
                # Only disable the hint button temporarily
                self.gui.hint_button.config(state="disabled")
            return None

        # Reduce hint count
        self.hint_counts[player_index] -= 1

        # Get hint using your existing code
        hint = Hint.find_best_move(self)
        if not hint:
            # Refund hint if none available
            self.hint_counts[player_index] += 1
            if self.gui:
                self.gui.update_status_text(
                    "No hint available for current situation."
                )
            return None

        hint_message = ""
        remaining = self.hint_counts[player_index]

        if hint["type"] == "select":
            worker = hint["worker"]
            hint_message = f"Hint: Select worker {worker.name} ({remaining} hints remaining)"
            if self.gui:
                self.gui.highlight_hint(worker.position)

        elif hint["type"] == "move":
            position = hint["position"]
            hint_message = f"Hint: Move to position {position} ({remaining} hints remaining)"
            if self.gui:
                self.gui.highlight_hint(position)

        elif hint["type"] == "build":
            position = hint["position"]
            hint_message = f"Hint: Build at position {position} ({remaining} hints remaining)"
            if self.gui:
                self.gui.highlight_hint(position)

        if self.gui:
            self.gui.update_status_text(hint_message)

        # Disable hint button only for this player if no hints left
        if self.hint_counts[player_index] == 0 and self.gui:
            self.gui.hint_button.config(state="disabled")
            self.gui.root.after(3000, lambda: self.gui.update_status_text(
                f"All hints for {self.get_current_player().name} have been used!"
            ))

        return hint


def main():
    root = Tk()
    try:
        _ = SantoriniGUI(root, Game)
        root.mainloop()
    except Exception as e:
        print(f"Error initializing GUI: {e}")
        root.destroy()
        return


if __name__ == "__main__":
    main()
