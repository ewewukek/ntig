import re

ANSI_SGR_RE = re.compile(r'^\033\[([0-9;]*)m')
BRIGHTEN_RE = re.compile(r'\033\[3([0-7])')
COLORS = {
    'default': '\033[39m',
    'black': '\033[30m',
    'red': '\033[31m',
    'green': '\033[32m',
    'yellow': '\033[33m',
    'blue': '\033[34m',
    'magenta': '\033[35m',
    'cyan': '\033[36m',
    'white': '\033[37m',
    'brightblack': '\033[90m',
    'bright-black': '\033[90m',
    'brightred': '\033[91m',
    'bright-red': '\033[91m',
    'brightgreen': '\033[92m',
    'bright-green': '\033[92m',
    'brightyellow': '\033[93m',
    'bright-yellow': '\033[93m',
    'brightblue': '\033[94m',
    'bright-blue': '\033[94m',
    'brightmagenta': '\033[95m',
    'bright-magenta': '\033[95m',
    'brightcyan': '\033[96m',
    'bright-cyan': '\033[96m',
    'brightwhite': '\033[97m',
    'bright-white': '\033[97m',
}


def brighten(string):
    if isinstance(string, AnsiString):
        s = AnsiString('')
        s.length = string.length
        s.parts = [brighten(x) for x in string.parts]
        return s

    return BRIGHTEN_RE.sub('\033[9\\g<1>', string)


class AnsiString:
    def __init__(self, line: str = ''):
        self.parts = []
        self.length = 0

        b = 0
        while b < len(line):
            e = line.find('\033', b)
            if e == -1:
                e = len(line)

            self.parts.append(line[b:e])
            self.length += e - b

            if e < len(line):
                if m := ANSI_SGR_RE.match(line[e:]):
                    self.parts.append(m.group(0))
                    e += len(m.group(0))
                else:
                    self.parts[-1] += '^'
                    e += 1
                    self.length += 1

            b = e

    def substr(self, index, length):
        sub = AnsiString('')

        skip = index
        for part in self.parts:
            if part[0:1] == '\033':
                sub.parts.append(part)
                continue

            if skip > 0:
                if skip <= len(part):
                    part = part[skip:]
                    skip = 0
                else:
                    skip -= len(part)

            if skip == 0:
                if sub.length + len(part) >= length:
                    sub.parts.append(part[:length-sub.length])
                    sub.length = length
                    break
                elif len(part) > 0:
                    sub.parts.append(part)
                    sub.length += len(part)

        if sub.length == 0:
            sub.parts = []

        return sub

    def __len__(self):
        return self.length

    def __str__(self):
        return ''.join(self.parts)

    def strip_colors(self):
        return ''.join(x for x in self.parts if x[0:1] != '\033')
