from PIL import ImageTk, Image
import os.path

class ChessPiece:
    IMG = ''
    def __init__(self, x, y, color=1, value=0):
        self.x = x
        self.y = y
        self.color = color # 1 = white, -1 = black; color can be used as move direction for pawns etc.
        self.value = value
        self.taken = False
        self.has_moved = False  # for king, rook, pawns
        self.pinned = False
        self.pinning = None
        self.legal_moves = []
        self.extended_moves = []  # these moves are blocked off by a piece, but may indicate a pin; only necessary for pieces that branch
        self.checking = []
        self._img = Image.open(os.path.join('img', self.IMG + '_' + ('w' if self.color == 1 else 'b') + '.png'))
        self.img = None  # see get_img()

    def get_img(self):
        # tkinter is finicky so we need to make the photoimage when main.py requests it, not before
        if self.img is None:
            self.img = ImageTk.PhotoImage(self._img)
        return self.img

    def update_legal_moves(self, board):
        # abstract method; override in each piece for their valid moves
        return

    def _update_legal_moves(self, board, theoretical=False):
        self.legal_moves = []
        self.checking = []
        self.extended_moves = []
        if self.taken:
            return
        self.update_legal_moves(board)
        self.legal_moves = tuple(xy for xy in self.legal_moves if self.on_board(*xy))
        if (not theoretical) and (checking := board.checking[self.color]):
            actual_legal_moves = []
            oldx = self.x
            oldy = self.y
            for move in self.legal_moves:
                taken_piece = self.move(*move, board.get(*move), force=True)
                board.update_legal_moves(theoretical=True)
                board.update_kings_checked()
                if not board.checking[self.color]:
                    actual_legal_moves.append(move)

                print(self.move(oldx, oldy, None, force=True))
                if type(taken_piece) is not bool:
                    taken_piece.taken = False
            self.legal_moves = tuple(actual_legal_moves)


    def check_move(self, x, y, taken_piece):
        return (not self.pinned) and (not self.taken) and (x, y) in self.legal_moves and ((taken_piece.color != self.color) if taken_piece is not None else True)

    def move(self, x, y, taken_piece, force=False) -> bool:
        if self.check_move(x, y, taken_piece) or force:
            self.x = x
            self.y = y
            self.has_moved = True
            if taken_piece is not None:
                taken_piece.taken = True
                return taken_piece
            return True
        return False

    def basic_move_calc(self, board, *coords, king=False):
        # throw in some move coordinates and see if they're basically legal
        legal_moves = []
        for xy in coords:
            if (taken := board.get(*xy)) is None and (board.legal_for_king(*xy, self.color) if king else True):
                legal_moves.append(xy)
            elif taken and taken.color != self.color:
                legal_moves.append(xy)
                self.checking.append(xy)
        return legal_moves

    def branch_move_calc(self, xoffset, yoffset, board):
        # Calculate moves going off in the direction of xoffset, yoffset; useful for rook, bishop, and queen
        branch = []
        x = self.x + xoffset
        y = self.y + yoffset

        while (blocker := board.get(x, y)) is None and self.on_board(x, y):
            branch.append((x, y))
            x += xoffset
            y += yoffset
        blockerx = x
        blockery = y
        while self.on_board(x, y):
            self.extended_moves.append((x, y))
            x += xoffset
            y += yoffset

        if blocker and blocker.color != self.color:  # if there's a blocker of another color then they're checked
            branch.append((blockerx, blockery))
            self.checking.append((blockerx, blockery))

            for xy in self.extended_moves:
                if (king := board.get(*xy)) and king.value == 0:
                    blocker.pinned = True
                    self.pinning = blocker  # pinning only happens for branch-style pieces
                    break
                elif king and king.value != 0:  # more than one piece are now between me and king
                    if self.pinning:
                        self.pinning.pinned = False
                        self.pinning = None
                    break
            else:  # there was an update and we discovered we no longer pin the piece; release it
                if self.pinning:
                    self.pinning.pinned = False
                    self.pinning = None

        return branch

    @classmethod
    def on_board(self, x, y=1):
        return 0 < x < 9 and 0 < y < 9


class Pawn(ChessPiece):
    IMG = 'pawn'
    def __init__(self, x, y, color=1):
        super().__init__(x, y, color=color, value=1)
        self.double_moved = False
        self.can_convert = False
        # EN PASSANT

    def update_legal_moves(self, board):
        # Pawn needs custom code for his move calculation because he's a special boy
        if board.get(self.x, self.y+self.color) is None:  # Move 1 space with nothing blocking
            self.legal_moves.append((self.x, self.y+self.color))
            if board.get(self.x, self.y + self.color * 2) is None and not self.has_moved:  # Move 2 space wth nothing blocking
                self.legal_moves.append((self.x, self.y+self.color*2))

        if (taken := board.get(self.x+1, self.y+self.color)) and taken.color != self.color:  # Take right
            self.legal_moves.append((self.x+1, self.y+self.color))
            self.checking.append((self.x+1, self.y+self.color))
        if (taken := board.get(self.x-1, self.y+self.color)) and taken.color != self.color:  # Take left
            self.legal_moves.append((self.x-1, self.y+self.color))
            self.checking.append((self.x-1, self.y+self.color))

    def move(self, x, y, taken_piece, force=False):
        self.double_moved = False
        if y == self.y + self.color*2:
            self.double_moved = True
        v = super().move(x, y, taken_piece, force=force)
        if self.y == 8 and self.color == 1 or self.y == 1 and self.color == -1:
            self.can_convert = True
        return v

    def convert(self, cls):
        new = cls(self.x, self.y, self.color)
        self.__class__ = cls
        self.__dict__ = new.__dict__

class Bishop(ChessPiece):
    IMG = 'bishop'
    def __init__(self, x, y, color=1):
        super().__init__(x, y, color=color, value=3)

    def update_legal_moves(self, board):
        self.legal_moves.extend(self.branch_move_calc(1, 1, board))
        self.legal_moves.extend(self.branch_move_calc(-1, 1, board))
        self.legal_moves.extend(self.branch_move_calc(1, -1, board))
        self.legal_moves.extend(self.branch_move_calc(-1, -1, board))

class Knight(ChessPiece):
    IMG = 'knight'
    def __init__(self, x, y, color=1):
        super().__init__(x, y, color=color, value=3)

    def update_legal_moves(self, board):
        possible = ((self.x+1, self.y+2), (self.x+2, self.y+1), (self.x+2, self.y-1), (self.x+1, self.y-2),
                    (self.x-1, self.y-2), (self.x-2, self.y-1), (self.x-2, self.y+1), (self.x-1, self.y+2))
        self.legal_moves.extend(self.basic_move_calc(board, *possible))

class Rook(ChessPiece):
    IMG = 'rook'
    def __init__(self, x, y, color=1):
        super().__init__(x, y, color=color, value=5)

    def update_legal_moves(self, board):
        self.legal_moves.extend(self.branch_move_calc(1, 0, board))
        self.legal_moves.extend(self.branch_move_calc(-1, 0, board))
        self.legal_moves.extend(self.branch_move_calc(0, 1, board))
        self.legal_moves.extend(self.branch_move_calc(0, -1, board))

class Queen(ChessPiece):
    IMG = 'queen'
    def __init__(self, x, y, color=1):
        super().__init__(x, y, color=color, value=9)

    def update_legal_moves(self, board):
        Bishop.update_legal_moves(self, board)
        Rook.update_legal_moves(self, board)

class King(ChessPiece):
    IMG = 'king'
    def __init__(self, x, y, color=1):
        super().__init__(x, y, color=color, value=0)

    def update_legal_moves(self, board):
        possible = ((self.x, self.y+1), (self.x+1, self.y+1), (self.x+1, self.y), (self.x+1, self.y-1),
                  (self.x, self.y-1), (self.x-1, self.y-1), (self.x-1, self.y), (self.x-1, self.y+1))

        self.legal_moves.extend(self.basic_move_calc(board, *possible, king=True))

        # CASTLE



SETUP_WHITE = [Pawn(i, 2) for i in range(1, 9)] + [Rook(1, 1), Rook(8, 1), Knight(2, 1), Knight(7, 1), Bishop(3, 1), Bishop(6, 1), Queen(5,1), King(4,1)]
SETUP_BLACK = [Pawn(i, 7, color=-1) for i in range(1, 9)] + [Rook(1, 8, color=-1), Rook(8, 8, color=-1), Knight(2, 8, color=-1), Knight(7, 8, color=-1), Bishop(3, 8, color=-1), Bishop(6, 8, color=-1), Queen(5, 8, color=-1), King(4, 8, color=-1)]
