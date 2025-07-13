import tkinter as tk
from tkinter import Canvas, Button, messagebox, simpledialog
import random


class SantoriniGUI:
    """GUI implementation for the Santorini game."""

    def __init__(self, root, game_factory):
        self.root = root
        self.root.title("Santorini Board Game")
        self.root.geometry("805x542")
        self.root.configure(bg="#FFFFFF")
        self.root.resizable(False, False)

        self.game_factory = game_factory
        self.game = None
        self.board_buttons = []
        self.highlighted_tiles = []
        self.skip_button = None

        self.level_colors = ["#FFFFFF", "#ADD8E6",
                             "#00FFFF", "#008000", "#808080"]

        self.setup_ui()
        self.new_game()

    def setup_ui(self):
        """Setup the UI elements."""
        self.canvas = Canvas(
            self.root,
            bg="#FFFFFF",
            height=542,
            width=805,
            bd=0,
            highlightthickness=0,
            relief="ridge",
        )
        self.canvas.place(x=0, y=0)

        self.canvas.create_rectangle(
            274.5189514160156,
            10.51898193359375,
            795.4810485839844,
            531.4810791015625,
            fill="#D9D9D9",
            outline="",
        )

        self.canvas.create_rectangle(
            9.76872730255127,
            10.268707275390625,
            260.2312364578247,
            260.73121643066406,
            fill="#D9D9D9",
            outline="",
        )

        self.canvas.create_rectangle(
            9.76872730255127,
            281.2687072753906,
            260.2312364578247,
            531.7312164306641,
            fill="#D9D9D9",
            outline="",
        )

        self.canvas.create_text(
            16.0,
            25.092559814453125,
            anchor="nw",
            text="Player 1",
            fill="#000000",
            font=("Inter", 24),
        )

        self.canvas.create_text(
            16.0,
            296.0925598144531,
            anchor="nw",
            text="Player 2",
            fill="#000000",
            font=("Inter", 24),
        )

        self.turn_text = self.canvas.create_text(
            16.0,
            54.0,
            anchor="nw",
            text="Your turn",
            fill="#000000",
            font=("Inter", 12),
        )

        self.p1_god_text = self.canvas.create_text(
            21.0,
            117.0,
            anchor="nw",
            text="Artemis",
            fill="#000000",
            font=("Inter", 16),
            tags=("p1_god_card",),
        )

        self.p2_god_text = self.canvas.create_text(
            21.0,
            387.4296569824219,
            anchor="nw",
            text="Demeter",
            fill="#000000",
            font=("Inter", 16),
            tags=("p2_god_card",),
        )

        self.canvas.tag_bind(
            "p1_god_card", "<Button-1>", lambda event: self.activate_god_power(
                0)
        )
        self.canvas.tag_bind(
            "p2_god_card", "<Button-1>", lambda event: self.activate_god_power(
                1)
        )

        self.canvas.create_text(
            199.0,
            25.0,
            anchor="nw",
            text="Builders",
            fill="#000000",
            font=("Inter Black", 12),
        )

        self.p1_color1 = self.canvas.create_rectangle(
            203.0, 40.0, 222.0, 59.070369720458984, fill="#00D0FF", outline=""
        )

        self.p1_color2 = self.canvas.create_rectangle(
            231.0, 40.0, 250.0, 59.070369720458984, fill="#0086A4", outline=""
        )

        self.canvas.create_text(
            199.0,
            296.0,
            anchor="nw",
            text="Builders",
            fill="#000000",
            font=("Inter Black", 12),
        )

        self.p2_color1 = self.canvas.create_rectangle(
            202.0, 311.0, 221.0, 330.070369720459, fill="#FF0088", outline=""
        )

        self.p2_color2 = self.canvas.create_rectangle(
            231.0, 311.0, 250.0, 330.070369720459, fill="#93004E", outline=""
        )

        self.status_text = self.canvas.create_text(
            16.0,
            200.0,
            anchor="nw",
            text="Welcome to Santorini!",
            fill="#000000",
            width=230,
            font=("Inter", 12),
        )

        self.hint_button = Button(
            self.root,
            text="Hint",
            command=self.show_hint,
            font=("Arial", 12, "bold"),  # Making it more visible
            bg="#FFC107",  # Gold color
            fg="#000000"
        )

        self.create_board_buttons()
        self.create_timer_displays()
        self.hint_button.place(x=20, y=460, width=100, height=35)

    def create_board_buttons(self):
        """Create the 5x5 grid of board buttons with level-based colors instead of images."""
        self.board_buttons = [[None for _ in range(5)] for _ in range(5)]

        start_x = 289.5
        start_y = 25.5
        button_width = 90
        button_height = 90
        button_spacing = 100

        for row in range(5):
            for col in range(5):
                x = start_x + col * button_spacing
                y = start_y + row * button_spacing

                btn = Button(
                    self.root,
                    text="Level 0",
                    borderwidth=1,
                    highlightthickness=0,
                    command=lambda r=row, c=col: self.handle_tile_click(r, c),
                    relief="raised",
                    bg=self.level_colors[0],
                    font=("Arial", 10),
                )
                btn.place(x=x, y=y, width=button_width, height=button_height)

                self.board_buttons[row][col] = btn

        self.skip_button = Button(
            self.root, text="Skip", command=self.skip_action)

    def handle_tile_click(self, row, col):
        """Handle a click on the game board."""
        self.game.handle_tile_click(row, col)

    def update_board(self):
        """Update the visual representation of the board."""
        for row in range(5):
            for col in range(5):
                btn = self.board_buttons[row][col]
                tile = self.game.board.grid[row][col]

                level_color = self.level_colors[tile.level.value]

                label_text = f"Level {tile.level.value}"
                if tile.is_dome():
                    label_text = "DOME"

                if tile.worker:
                    player = tile.worker.player
                    worker_color = player.color
                    btn.config(
                        text=f"{label_text}\n{tile.worker.name}",
                        bg=worker_color,
                        fg="#FFFFFF" if tile.level.value >= 3 else "#000000",
                    )
                else:
                    btn.config(
                        text=label_text,
                        bg=level_color,
                        fg="#FFFFFF" if tile.level.value >= 3 else "#000000",
                    )

    def highlight_tiles(self, positions, color="#90EE90"):
        """Highlight board tiles to show valid moves or builds."""
        self.clear_highlights()

        for row, col in positions:
            btn = self.board_buttons[row][col]
            current_bg = btn.cget("bg")
            self.highlighted_tiles.append((btn, current_bg))
            btn.config(highlightbackground=color, highlightthickness=3)

    def clear_highlights(self):
        """Remove highlighting from tiles."""
        for btn, original_bg in self.highlighted_tiles:
            btn.config(highlightthickness=0)
        self.highlighted_tiles = []

    def update_status_text(self, message):
        """Update the status message area."""
        self.canvas.itemconfig(self.status_text, text=message)

    def update_turn_indicator(self):
        """Update the turn indicator text."""
        current_player = self.game.get_current_player()
        self.canvas.itemconfig(
            self.turn_text, text=f"{current_player.name}'s turn")

        if self.game.current_player_index == 0:
            self.canvas.itemconfig(self.p1_god_text, fill="#0000FF")
            self.canvas.itemconfig(self.p2_god_text, fill="#000000")
        else:
            self.canvas.itemconfig(self.p1_god_text, fill="#000000")
            self.canvas.itemconfig(self.p2_god_text, fill="#0000FF")

    def show_skip_button(self):
        """Show the skip button for optional god power actions."""
        self.skip_button.place(x=75, y=460, width=100, height=25)

    def hide_skip_button(self):
        """Hide the skip button."""
        self.skip_button.place_forget()

    def skip_action(self):
        """Handle skip button click."""
        self.game.skip_second_action()

    def show_game_over(self, message):
        """Show game over dialog."""
        self.game.stop_timer()

        messagebox.showinfo("Game Over", message)
        if messagebox.askyesno("Game Over", "Start a new game?"):
            self.new_game()

    def new_game(self):
        """Start a new game."""
        self.game = self.game_factory(self)

        p1_name = (
            simpledialog.askstring(
                "Player 1", "Enter name for Player 1:", initialvalue="Player 1"
            )
            or "Player 1"
        )
        p2_name = (
            simpledialog.askstring(
                "Player 2", "Enter name for Player 2:", initialvalue="Player 2"
            )
            or "Player 2"
        )

        # Import these locally to avoid circular imports
        from main import Artemis, Demeter, Zeus
        zeus=Zeus()
        god_cards = [Artemis(), Demeter()]
        random.shuffle(god_cards)
        if random.choice([True,False]):
            p1_card=zeus
            p2_card=god_cards[0]
        else:
            p1_card=god_cards[0]
            p2_card=zeus
        self.canvas.itemconfig(self.p1_god_text, text=p1_card.name)
        self.canvas.itemconfig(self.p2_god_text, text=p2_card.name)

        self.game.add_player(p1_name, p1_card, "#00D0FF")
        self.game.add_player(p2_name, p2_card, "#FF0088")

        self.clear_highlights()
        self.update_board()
        self.update_turn_indicator()
        self.game.start_game()

    def activate_god_power(self, player_index):
        """Activate god power when god card is clicked."""
        if self.game.current_player_index == player_index:
            if self.game.activate_god_power():
                if player_index == 0:
                    self.canvas.itemconfig(self.p1_god_text, fill="#FF0000")
                else:
                    self.canvas.itemconfig(self.p2_god_text, fill="#FF0000")

    def create_timer_displays(self):
        """Create timer displays for both players."""
        # Player 1 timer
        self.p1_timer_frame = tk.Frame(self.root, bg="#D9D9D9")
        self.p1_timer_frame.place(x=16, y=85, width=230)

        self.p1_timer_label = tk.Label(
            self.p1_timer_frame,
            text="Time:",
            font=("Inter", 12, "bold"),
            bg="#D9D9D9",
            fg="#000000"
        )
        self.p1_timer_label.pack(side=tk.LEFT, padx=5)

        self.p1_timer_display = tk.Label(
            self.p1_timer_frame,
            text="15:00",
            font=("Inter", 14, "bold"),
            bg="#D9D9D9",
            fg="#000000"
        )
        self.p1_timer_display.pack(side=tk.RIGHT, padx=5)

        # Player 2 timer
        self.p2_timer_frame = tk.Frame(self.root, bg="#D9D9D9")
        self.p2_timer_frame.place(x=16, y=355, width=230)

        self.p2_timer_label = tk.Label(
            self.p2_timer_frame,
            text="Time:",
            font=("Inter", 12, "bold"),
            bg="#D9D9D9",
            fg="#000000"
        )
        self.p2_timer_label.pack(side=tk.LEFT, padx=5)

        self.p2_timer_display = tk.Label(
            self.p2_timer_frame,
            text="15:00",
            font=("Inter", 14, "bold"),
            bg="#D9D9D9",
            fg="#000000"
        )
        self.p2_timer_display.pack(side=tk.RIGHT, padx=5)

    def update_timer_display(self):
        """Update both player timer displays."""
        if not hasattr(self, 'p1_timer_display') or not self.game or not self.game.timer:
            return

        # Update Player 1 timer
        p1_time = self.game.get_timer_display(0)
        self.p1_timer_display.config(text=p1_time)

        # Update Player 2 timer
        p2_time = self.game.get_timer_display(1)
        self.p2_timer_display.config(text=p2_time)

        # Highlight active timer
        if self.game.timer.running:
            if self.game.current_player_index == 0:
                self.p1_timer_display.config(fg="#0000FF")
                self.p2_timer_display.config(fg="#000000")
            else:
                self.p1_timer_display.config(fg="#000000")
                self.p2_timer_display.config(fg="#0000FF")

        # Change color when time is running low
        p1_seconds = int(self.game.timer.player_timers[0])
        if p1_seconds <= 60:
            self.p1_timer_display.config(fg="#FF0000")
        elif p1_seconds <= 180:
            self.p1_timer_display.config(fg="#FF8C00")

        p2_seconds = int(self.game.timer.player_timers[1])
        if p2_seconds <= 60:
            self.p2_timer_display.config(fg="#FF0000")
        elif p2_seconds <= 180:
            self.p2_timer_display.config(fg="#FF8C00")

    def show_hint(self):
        """Show a hint for the best move."""
        if self.game and not self.game.winner:
            if not hasattr(self.game, 'hint_counts'):
                self.game.hint_counts = [3, 3]

            player_index = self.game.current_player_index

            # Disable button if no hints remaining
            if self.game.hint_counts[player_index] <= 0:
                self.hint_button.config(state="disabled")
                self.game.gui.update_status_text(
                    "No hints remaining for this player.")
                return

        self.game.provide_hint()

    def highlight_hint(self, position):
        """Highlight the position for the hint."""
        self.clear_highlights()
        row, col = position
        btn = self.board_buttons[row][col]

        # Store original background
        original_bg = btn.cget("bg")
        self.highlighted_tiles.append((btn, original_bg))

        # Use gold color for hints
        btn.config(bg="#FFC107")
