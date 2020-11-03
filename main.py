from tkinter import *
import pieces
from board import ChessBoard

root = Tk()
root.title('Board Game')
root.configure(bg='#222')

sq = 64
bw = sq*8
bh = sq*8
w = bw + 64
h = bh + 128
root.geometry('{}x{}'.format(w, h))

canvas = Canvas(root, width=bw, height=bh, bg='#222', highlightthickness=0)
canvas.place(x=0, y=0)

WHITE = '#FDB'
BLACK = '#653'
HIGHLIGHT_W = '#FDF'
HIGHLIGHT_B = '#657'

squares = {}
square_colors = {}
counter = 1
for x in range(1, 9):
    counter = -counter
    for y in range(1, 9):
        counter = -counter
        squares[(x,y)] = canvas.create_rectangle((x-1)*sq, (y-1)*sq, (x)*sq, (y)*sq, fill=WHITE if counter == 1 else BLACK, outline='')
        square_colors[(x,y)] = counter

highlighted_squares = []
dehighlight_squares = []
dehighlight = False
selected: pieces.ChessPiece = None

board = ChessBoard()
for piece in pieces.SETUP_WHITE + pieces.SETUP_BLACK:
    board.add_piece(piece)

board.update_legal_moves()

for row in board.board:
    print(row)


sprites = [canvas.create_image((p.x*sq-sq//2, p.y*sq-sq//2), image=p.get_img()) for p in board.pieces]

def select_square(e):
    global dehighlight, selected
    dehighlight = False
    x, y = e.x // sq + 1, e.y // sq + 1
    print(x,y)

    highlighted_squares.append((x, y))

    selected = board.get(x, y)
    if selected:
        for xy in selected.legal_moves:
            highlighted_squares.append(xy)

    dehighlight_squares.extend(highlighted_squares)

def deselect_square(e):
    global dehighlight
    dehighlight = True

    x, y = e.x // sq + 1, e.y // sq + 1
    print(x,y)
    if selected and board.move_piece(selected.x, selected.y, x, y):
        print("UPDATE")
        board.update_legal_moves()
        board.update_kings_checked()

root.bind('<Button-1>', select_square)
root.bind('<ButtonRelease-1>', deselect_square)


# mainloop
try:
    while True:
        for _ in range(len(highlighted_squares)):
            xy = highlighted_squares.pop()
            x, y = xy
            canvas.delete(squares[xy])
            squares[xy] = canvas.create_rectangle((x-1) * sq, (y-1) * sq, (x) * sq, (y) * sq,
                                                  fill=HIGHLIGHT_W if square_colors[xy] == 1 else HIGHLIGHT_B,
                                                  outline='')

        if dehighlight:
            for _ in range(len(dehighlight_squares)):
                xy = dehighlight_squares.pop()
                x, y = xy
                canvas.delete(squares[xy])
                squares[xy] = canvas.create_rectangle((x-1) * sq, (y-1) * sq, (x) * sq, (y) * sq,
                                                      fill=WHITE if square_colors[xy] == 1 else BLACK, outline='')

        for sprite in sprites:
            canvas.delete(sprite)
        sprites = [canvas.create_image((p.x * sq - sq // 2, p.y * sq - sq // 2), image=p.get_img()) for p in
                   board.pieces if not p.taken]

        root.update()
        root.update_idletasks()
        canvas.update()
        canvas.update_idletasks()
except (TclError, KeyboardInterrupt, SystemExit):
    print('Application destroyed.')