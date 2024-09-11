#!/usr/bin/env python

from ansi_string import brighten, COLORS
from datetime import datetime
from screen import Screen, SelectionScreen
import argparse
import re
import shlex
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
    if old_attrs:
        termios.tcsetattr(tty_fd, termios.TCSADRAIN, old_attrs)


def signal_handler(sig, frame):
    if sig == signal.SIGWINCH:
        if screen:
            screen.update_size(True)
    else:
        restore_terminal()
        exit()


def load_log(cfg):
    try:
        data = subprocess.check_output([
            'git',
            'log',
            '--graph',
            '--color',
            *cfg['log_args'],
            '--pretty=format:%ad %aN %h %s',
            '--date=format:%s'
        ])

        if '{refs}' in cfg['log_fmt']:
            refs_data = subprocess.check_output(['git', 'show-ref', '--head'])
        else:
            refs_data = b''

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
            'refs': '',
            'message': '',
        }
        if m := log_line_re.match(line):
            g = m.group(1)
            d = datetime.fromtimestamp(int(m.group(2)))
            commit['date'] = d.strftime(cfg['date_fmt'])
            commit['author'] = m.group(3)
            commit['id'] = commit['hash'] = m.group(4)
            commit['message'] = m.group(5)
        else:
            g = line

        g = g.strip()
        g = brighten(g)
        if cfg['node_color'] != COLORS['default']:
            g = g.replace('*', cfg['node_color'] + '*' + COLORS['default'])
        g = g.replace('\033[m', '\033[39m')
        commit['graph'] = g

        for field in ['date', 'author', 'hash']:
            lengths[field] = max(lengths[field], len(commit[field]))

        log.append(commit)

    refs = {}
    refs_line_re = re.compile(r'^([0-9a-f]{40,}) (.*)$')
    for line in refs_data.splitlines():
        line = line.decode('utf8')

        m = refs_line_re.match(line)
        h = m.group(1)[0:lengths['hash']]
        if h not in refs:
            refs[h] = {}

        ref = m.group(2)
        if ref == 'HEAD':
            if cfg['decorate']:
                ref = '[' + ref + ']'
            refs[h]['head'] = [ref]

        elif ref[0:11] == 'refs/heads/':
            if 'branch' not in refs[h]:
                refs[h]['branch'] = []
            ref = ref[11:]
            if cfg['decorate']:
                ref = '[' + ref + ']'
            refs[h]['branch'].append(ref)

        elif ref[0:13] == 'refs/remotes/':
            if 'remote' not in refs[h]:
                refs[h]['remote'] = []
            ref = ref[13:]
            if cfg['decorate']:
                ref = '{' + ref + '}'
            refs[h]['remote'].append(ref)

        elif ref[0:10] == 'refs/tags/':
            if 'tag' not in refs[h]:
                refs[h]['tag'] = []
            ref = ref[10:]
            if cfg['decorate']:
                ref = '<' + ref + '>'
            refs[h]['tag'].append(ref)

        elif ref == 'refs/stash':
            if cfg['decorate']:
                ref = '[' + ref + ']'
            refs[h]['stash'] = [ref]

    for commit in log:
        if commit['hash'] in refs:
            ref = refs[commit['hash']]
            parts = []
            for field in ['head', 'branch', 'tag', 'remote', 'stash']:
                if field in ref:
                    part = ' '.join(ref[field])
                    color = cfg[f'{field}_color']
                    if color != COLORS['default']:
                        part = color + part + '\033[39m'
                    parts.append(part)

            commit['refs'] = ' '.join(parts)
            if cfg['refs_bold']:
                commit['refs'] = '\033[1m' + commit['refs'] + '\033[22m'
            commit['refs'] += ' '

        for field in ['date', 'author', 'hash']:
            color = cfg[f'{field}_color']
            if color != COLORS['default']:
                commit[field] = (
                    color + commit[field] + COLORS['default']
                    + ' ' * (lengths[field] - len(commit[field])))
            else:
                commit[field] = commit[field].ljust(lengths[field])

    return log


def show_commit(cfg, hash):
    git_cmd = ['git', 'show', '--color', hash]
    if cfg['pager']:
        p = subprocess.Popen(git_cmd, stdout=subprocess.PIPE)
        data = subprocess.check_output(cfg['pager'], stdin=p.stdout)
        p.wait()
    else:
        data = subprocess.check_output(git_cmd)

    global screen
    prev_screen = screen
    screen = Screen(data.splitlines())
    screen.input_loop()
    screen = prev_screen


def parse_arguments():
    parser = argparse.ArgumentParser(
        'ntig',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog='other options will be passed to git log')
    parser.add_argument(
        '--ntig-hash',
        help='hash color',
        dest='hash_color',
        default='yellow',
        metavar='')
    parser.add_argument(
        '--ntig-date',
        help='date color',
        dest='date_color',
        default='default',
        metavar='')
    parser.add_argument(
        '--ntig-date-fmt',
        help='date format',
        dest='date_fmt',
        default='%d %b %H:%M',
        metavar='')
    parser.add_argument(
        '--ntig-author',
        help='author name color',
        dest='author_color',
        default='cyan',
        metavar='')
    parser.add_argument(
        '--ntig-node',
        help='graph node color',
        dest='node_color',
        default='bright-yellow',
        metavar='')

    parser.add_argument(
        '--ntig-head',
        help='HEAD color',
        dest='head_color',
        default='bright-cyan',
        metavar='')
    parser.add_argument(
        '--ntig-branch',
        help='local branch color',
        dest='branch_color',
        default='bright-green',
        metavar='')
    parser.add_argument(
        '--ntig-remote',
        help='remote branch color',
        dest='remote_color',
        default='bright-red',
        metavar='')
    parser.add_argument(
        '--ntig-tag',
        help='tag color',
        dest='tag_color',
        default='bright-yellow',
        metavar='')
    parser.add_argument(
        '--ntig-stash',
        help='stash color',
        dest='stash_color',
        default='bright-blue',
        metavar='')
    parser.add_argument(
        '--ntig-refs-bold',
        help='show refs in bold',
        action='store_true',
        dest='refs_bold')
    parser.add_argument(
        '--ntig-decorate',
        help='decorate refs',
        action='store_true',
        dest='decorate')

    parser.add_argument(
        '--ntig-log',
        help='log format',
        dest='log_fmt',
        default='{hash} {date} {author} {graph} {refs}{message}',
        metavar='')
    parser.add_argument(
        '--ntig-pager',
        help='pager to pipe output of git show',
        dest='pager',
        default='none',
        metavar='')

    args, unknown = parser.parse_known_args()
    cfg = vars(args)
    cfg['log_args'] = unknown

    if cfg['pager'] == 'none':
        cfg['pager'] = None
    else:
        cfg['pager'] = shlex.split(cfg['pager'])

    for field in ['hash_color', 'date_color', 'author_color', 'node_color',
                  'head_color', 'branch_color', 'remote_color',
                  'tag_color', 'stash_color']:
        color = cfg[field]
        if not color.strip():
            color = 'default'
        if color[0:4] == '\\033':
            color = '\033' + color[4:]
        if color[0:1] != '\033':
            if color in COLORS:
                color = COLORS[color]
            else:
                print(f'unrecognized color: {color}', file=sys.stderr)
                exit(1)
        cfg[field] = color

    return cfg


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGWINCH, signal_handler)

try:
    cfg = parse_arguments()
    log = load_log(cfg)

    init_terminal()

    def action_fn(i):
        if log[i]['id']:
            show_commit(cfg, log[i]['id'])

    log_lines = [cfg['log_fmt'].format(**c) for c in log]
    screen = SelectionScreen(log_lines, action_fn)
    screen.input_loop()

    restore_terminal()
except Exception:
    restore_terminal()
    print(traceback.format_exc())
