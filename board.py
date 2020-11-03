import pieces

class ChessBoard:
    RANK = 'ABCDEFGH'

    def __init__(self):
        self.dimx = 8
        self.dimy = 8
        self.board = [[None]*self.dimx for _ in range(self.dimy)]
        self.pieces = []
        self.checking = {1: [], -1: []}
        self.kings = {1: None, -1: None}
        self.game_record = []

    @classmethod
    def on_board(self, x, y=1):
        return 0 < x < 9 and 0 < y < 9

    def add_piece(self, obj):
        self.pieces.append(obj)
        if obj.value == 0:
            self.kings[obj.color] = obj
        self.set(obj.x, obj.y, obj)

    def get(self, x, y):
        if self.on_board(x, y):
            return self.board[y-1][x-1]
        return None
    def set(self, x, y, obj):
        if self.on_board(x, y):
            self.board[y-1][x-1] = obj
            return obj
        return None

    def resolve_rf(self, rfstr):
        return self.RANK.index(rfstr[0].upper()), int(rfstr[1])
    def get_rf(self, rf):
        # rf is rank and file – A1 through H8
        return self.get(*self.resolve_rf(rf))
    def set_rf(self, rf, obj):
        self.set(*self.resolve_rf(rf), obj)

    def move_piece(self, x1, y1, x2, y2):
        piece: pieces.ChessPiece = self.get(x1, y1)
        taken_piece: pieces.ChessPiece = self.get(x2, y2)
        if piece is None:
            return False
        if piece.move(x2, y2, taken_piece):
            self.set(x1, y1, None)
            self.set(x2, y2, piece)
            return True
        return False

    def update_legal_moves(self, theoretical=False):
        for piece in self.pieces:
            piece._update_legal_moves(self, theoretical=theoretical)

    def update_kings_checked(self):
        piece: pieces.ChessPiece
        for list_ in self.checking.values():
            list_.clear()
        for piece in self.pieces:
            for checked in piece.checking:
                cp = self.get(*checked)
                if cp and cp.value == 0:  # king
                    self.checking[cp.color].append(piece)

    def legal_for_king(self, x, y, king_color):
        for piece in self.pieces:
            if piece.color != king_color and (((x,y) in piece.legal_moves and piece.value != 1) or\
                                              (y == piece.y + piece.color and (x == piece.x + 1 or x == piece.x - 1))):
                return False
        return True
