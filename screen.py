from ansi_string import AnsiString
import os
import sys

input_map = {
    '\03': 'q',  # ctrl + c
    '\04': 'q',  # ctrl + d
    '\015': '\n',
    '\033': {
        '\033': 'escape',
        '[': {
            'A': 'up',
            'B': 'down',
            'C': 'right',
            'D': 'left',
            '5': {'~': 'pgup'},
            '6': {'~': 'pgdn'},
            'H': 'home',
            'F': 'end',
        },
    },
}
move_top_left = '\033[H'
clear_to_bottom = '\033[J'
clear_to_right = '\033[K'
reset_graphics = '\033[m'
enable_inverse_colors = '\033[7m'
disable_inverse_colors = '\033[27m'


def read_input():
    i = input_map
    while True:
        c = sys.stdin.read(1)
        i = i.get(c, c)
        if isinstance(i, str):
            return i


class Screen:
    def __init__(self, lines: list):
        self.x = 0
        self.y = 0
        self.max_length = 0
        self.lines = []

        for line in lines:
            if isinstance(line, bytes):
                line = line.decode('utf8')
            if isinstance(line, str):
                line = AnsiString(line)
            if len(line) > self.max_length:
                self.max_length = len(line)
            self.lines.append(line)

        self.width = 0
        self.height = 0
        self.update_size()

    def draw(self):
        buf = [move_top_left]

        self.x = max(0, min(self.max_length - self.width, self.x))
        self.y = max(0, min(len(self.lines) - self.height, self.y))

        for y in range(self.height):
            i = self.y + y
            if i >= len(self.lines):
                buf.append(clear_to_bottom)
                break

            line = self.lines[i].substr(self.x, self.width)

            buf.append(reset_graphics)

            if hasattr(self, 'selected') and i == self.selected:
                buf.append(enable_inverse_colors)
                line.parts.append(' ' * (self.width - len(line)))

            buf.append(str(line))

            if hasattr(self, 'selected') and i == self.selected:
                buf.append(disable_inverse_colors)

            buf.append(clear_to_right)

            if y < self.height - 1:
                buf.append('\r\n')

        sys.stdout.write(''.join(buf))
        sys.stdout.flush()

    def input_loop(self):
        while True:
            self.draw()

            i = read_input()
            if i == 'q' or i == 'Q' or i == '\n':
                return
            if i == 'left':
                self.x -= self.width // 2
            if i == 'right':
                self.x += self.width // 2
            if i == 'up':
                self.y -= 1
            if i == 'down':
                self.y += 1
            if i == 'pgup':
                self.y -= self.height - 1
            if i == 'pgdn':
                self.y += self.height - 1

    def update_size(self, redraw=False):
        size = os.get_terminal_size()
        self.width = size.columns
        self.height = size.lines
        if redraw:
            self.draw()


class SelectionScreen(Screen):
    def __init__(self, lines: list, action_fn: callable):
        super().__init__(lines)
        self.selected = 0
        self.action_fn = action_fn

    def input_loop(self):
        while True:
            self.draw()

            i = read_input()
            if i == '\n':
                self.action_fn(self.selected)
            if i == 'q' or i == 'Q':
                return
            if i == 'left':
                self.x -= self.width // 2
            if i == 'right':
                self.x += self.width // 2
            if i == 'up':
                self.selected -= 1
            if i == 'down':
                self.selected += 1
            if i == 'pgup':
                if self.selected > self.y:
                    self.selected = self.y
                else:
                    self.selected -= self.height - 1
            if i == 'pgdn':
                if self.selected < self.y + self.height - 1:
                    self.selected = self.y + self.height - 1
                else:
                    self.selected += self.height - 1

            self.selected = max(0, min(len(self.lines), self.selected))
            if self.selected < self.y:
                self.y = self.selected
            if self.selected > self.y + self.height - 1:
                self.y = self.selected - self.height + 1
