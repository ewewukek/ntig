from ansi_string import brighten, COLORS
from datetime import datetime
from screen import Screen, SelectionScreen
import re
import signal
import subprocess
import sys
import termios
import traceback
import tty

tty_fd = sys.stdout.fileno()
old_attrs = None
screen = None


def init_terminal():
    global old_attrs
    old_attrs = termios.tcgetattr(tty_fd)
    tty.setraw(tty_fd)
    sys.stdout.write('\033[?1049h\033[?25l')


def restore_terminal():
    sys.stdout.write('\033[?1049l\033[?25h')
    termios.tcsetattr(tty_fd, termios.TCSADRAIN, old_attrs)


def signal_handler(sig, frame):
    if sig == signal.SIGWINCH:
        if screen:
            screen.update_size(True)
    else:
        restore_terminal()
        sys.exit()


def load_log(cfg):
    try:
        data = subprocess.check_output([
            'git',
            'log',
            '--graph',
            '--color',
            '--pretty=format:%ad %aN %h %s',
            '--date=format:%s'
        ])
    except subprocess.CalledProcessError as e:
        if e.output:
            print(e.output)
        exit(1)

    log = []
    log_line_re = re.compile(r'^(.*?) (\d+) (.*?) ([0-9a-f]{7,}) (.*)$')
    lengths = {
        'hash': 0,
        'date': 0,
        'author': 12,
    }

    for line in data.splitlines():
        line = line.decode('utf8')
        commit = {
            'id': None,
            'date': '',
            'author': '',
            'hash': '',
            'message': '',
        }
        if m := log_line_re.match(line):
            g = m.group(1)
            d = datetime.fromtimestamp(int(m.group(2)))
            commit['date'] = d.strftime('%d %b %H:%M')
            commit['author'] = m.group(3)
            commit['id'] = commit['hash'] = m.group(4)
            commit['message'] = m.group(5)
        else:
            g = line

        g = g.strip()
        g = brighten(g)
        g = g.replace('*', '\033[93m•\033[39m')
        g = g.replace('\033[m', '\033[39m')
        commit['graph'] = g

        for field in ['date', 'author', 'hash']:
            lengths[field] = max(lengths[field], len(commit[field]))

        log.append(commit)

    for commit in log:
        for field in ['date', 'author', 'hash']:
            color = cfg[f'{field}_color']
            if color and color[0:1] != '\033':
                color = COLORS[color]
            if color:
                commit[field] = (color + commit[field] + COLORS['default']
                                 + ' ' * (lengths[field] - len(commit[field])))
            else:
                commit[field] = commit[field].ljust(lengths[field])

    return log


def show_commit(h):
    p = subprocess.Popen(['git', 'show', '--color', h], stdout=subprocess.PIPE)
    data = subprocess.check_output(['delta', '--color-only'], stdin=p.stdout)
    p.wait()

    global screen
    prev_screen = screen
    screen = Screen(data.splitlines())
    screen.input_loop()
    screen = prev_screen


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGWINCH, signal_handler)

try:
    cfg = {
        'hash_color': COLORS['yellow'],
        'author_color': COLORS['cyan'],
        'date_color': '',
        'log_fmt': '{hash} {date} {author} {graph} {message}',
    }

    log = load_log(cfg)

    init_terminal()

    def action_fn(i):
        if log[i]['id']:
            show_commit(log[i]['id'])

    log_lines = [cfg['log_fmt'].format(**c) for c in log]
    screen = SelectionScreen(log_lines, action_fn)
    screen.input_loop()

    restore_terminal()
except Exception:
    restore_terminal()
    print(traceback.format_exc())
