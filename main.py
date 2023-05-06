from random import choice, random
from turtle import *

from freegames import vector

def value():
    """Randomly generate value between (-5, -3) or (3, 5)."""
    return (3 + random() * 2) * choice([1, -1])

ball = vector(0, 0)
aim = vector(value(), value())
state = {1: 0, 2: 0}

def move(player, change):
    """Move player position by change and limit paddle within the game boundary."""
    new_position = state[player] + change

    # Check if new position is within boundary
    if -200 <= new_position <= 100:
        state[player] = new_position

def rectangle(x, y, width, height):
    """Draw rectangle at (x, y) with given width and height."""
    up()
    goto(x, y)
    down()
    begin_fill()
    for count in range(2):
        forward(width)
        left(90)
        forward(height)
        left(90)
    end_fill()

def draw_border():
    up()
    goto(-210, 210)
    down()
    for _ in range(4):
        forward(420)
        right(90)

def reset_game():
    global ball, aim, state
    ball = vector(0, 0)
    aim = vector(value(), value())
    state = {1: 0, 2: 0}
    draw()

def draw():
    """Draw game and move pong ball."""
    clear()
    draw_border()
    rectangle(-200, state[1], 10, 100)
    rectangle(190, state[2], 10, 100)

    ball.move(aim)
    x = ball.x
    y = ball.y

    up()
    goto(x, y)
    dot(10)
    update()

    if y < -200 or y > 200:
        aim.y = -aim.y

    if x < -185:
        low = state[1] - 50
        high = state[1] + 100

        if low <= y <= high:
            aim.x = -aim.x
        else:
            display_text("Player 2 wins!", 0, 0, 24)  # 添加这一行
            display_text("Press Enter to restart", 0, -30, 16)  # 添加这一行
            onkey(reset_game, "Return")
            return

    if x > 185:
        low = state[2] - 50
        high = state[2] + 100

        if low <= y <= high:
            aim.x = -aim.x
        else:
            display_text("Player 1 wins!", 0, 0, 24)  # 添加这一行
            display_text("Press Enter to restart", 0, -30, 16)  # 添加这一行
            onkey(reset_game, "Return")
            return

    ontimer(draw, 50)
  
def display_text(text, x, y, size):
    """Display text at (x, y) with the given font size."""
    up()
    goto(x, y)
    down()
    color("black")
    write(text, align="center", font=("Arial", size, "normal"))


setup(420, 420, 370, 0)
hideturtle()
tracer(False)
listen()

bgcolor("white")
pencolor("black")

onkey(lambda: move(1, 20), 'w')
onkey(lambda: move(1, -20), 's')
onkey(lambda: move(2, 20), 'i')
onkey(lambda: move(2, -20), 'k')
draw()
done()