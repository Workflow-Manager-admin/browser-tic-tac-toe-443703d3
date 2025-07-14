from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

# PUBLIC_INTERFACE
class MoveRequest(BaseModel):
    """Request body for making a move in the tic tac toe game."""
    row: int = Field(..., ge=0, le=2, description="Row index (0-2)")
    col: int = Field(..., ge=0, le=2, description="Column index (0-2)")

# PUBLIC_INTERFACE
class GameStatusResponse(BaseModel):
    """Response body for game state and status."""
    board: List[List[Optional[str]]] = Field(..., description="3x3 game board: X, O, or None")
    current_player: Literal["X", "O"] = Field(..., description="Player whose move is next")
    winner: Optional[Literal["X", "O"]] = Field(None, description="Winner of the game, if any")
    draw: bool = Field(..., description="True if game is a draw")
    status: str = Field(..., description="Game status message")

app = FastAPI(
    title="Tic Tac Toe API",
    description="Backend logic and state for a simple two-player tic tac toe game.",
    version="1.0.0",
    openapi_tags=[
        {"name": "game", "description": "Tic Tac Toe Game Operations"}
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_new_board():
    # Returns a new, empty 3x3 board
    return [[None for _ in range(3)] for _ in range(3)]

class GameState:
    """Singleton game state for the in-memory tic tac toe board (1 game for all users)."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.board = get_new_board()
        self.current_player = "X"
        self.winner = None
        self.draw = False

    def make_move(self, row: int, col: int):
        if self.board[row][col] is not None or self.winner or self.draw:
            raise ValueError("Invalid move.")
        self.board[row][col] = self.current_player
        self.update_game_status()
        if not self.winner and not self.draw:
            self.current_player = "O" if self.current_player == "X" else "X"

    def update_game_status(self):
        # Check for win
        lines = []
        # rows and columns
        lines.extend(self.board)
        lines.extend([[self.board[r][c] for r in range(3)] for c in range(3)])
        # diagonals
        lines.append([self.board[i][i] for i in range(3)])
        lines.append([self.board[i][2 - i] for i in range(3)])
        for line in lines:
            if line[0] is not None and all(cell == line[0] for cell in line):
                self.winner = line[0]
                self.draw = False
                return
        # Check for draw
        if all(self.board[r][c] is not None for r in range(3) for c in range(3)):
            self.draw = True
            self.winner = None
        else:
            self.winner = None
            self.draw = False

    def get_status(self) -> GameStatusResponse:
        if self.winner:
            status = f"Player {self.winner} wins!"
        elif self.draw:
            status = "It's a draw!"
        else:
            status = f"Player {self.current_player}'s turn"
        return GameStatusResponse(
            board=self.board,
            current_player=self.current_player,
            winner=self.winner,
            draw=self.draw,
            status=status,
        )

# Single game instance for all users of the backend (no user management)
game_state = GameState()

# PUBLIC_INTERFACE
@app.get("/", tags=["game"])
def health_check():
    """Health check endpoint for backend."""
    return {"message": "Healthy"}

# PUBLIC_INTERFACE
@app.get("/game", response_model=GameStatusResponse, tags=["game"], summary="Get current game state", description="Returns the state of the tic tac toe board and active game status.")
def get_game_state():
    """Returns the current tic tac toe game state, including board, player turn, winner/draw status."""
    return game_state.get_status()

# PUBLIC_INTERFACE
@app.post("/move", response_model=GameStatusResponse, tags=["game"], summary="Make a move", description="Make a move at the given (row, col) as the current player. Returns updated game state.")
def make_move(move: MoveRequest):
    """
    Make a move as the current player.

    Args:
        move: MoveRequest with row and col indices (0-based).

    Returns:
        Updated game state.
    """
    if move.row < 0 or move.row > 2 or move.col < 0 or move.col > 2:
        raise HTTPException(status_code=400, detail="Invalid row or column. Must be 0, 1, or 2.")
    try:
        game_state.make_move(move.row, move.col)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid move. Try a different cell or reset the game.")
    return game_state.get_status()

# PUBLIC_INTERFACE
@app.post("/reset", response_model=GameStatusResponse, tags=["game"], summary="Reset game", description="Resets the board and game state to initial conditions. Useful to start a new game.")
def reset_game():
    """
    Resets the tic tac toe game.

    Returns:
        The fresh, empty game state.
    """
    game_state.reset()
    return game_state.get_status()
