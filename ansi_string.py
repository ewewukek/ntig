import re

ANSI_SGR_RE = re.compile(r'^\033\[([0-9;]*)m')
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
    'bright-black': '\033[90m',
    'bright-red': '\033[91m',
    'bright-green': '\033[92m',
    'bright-yellow': '\033[93m',
    'bright-blue': '\033[94m',
    'bright-magenta': '\033[95m',
    'bright-cyan': '\033[96m',
    'bright-white': '\033[97m',
}


def brighten(string):
    if isinstance(string, AnsiString):
        s = AnsiString('')
        s.length = string.length
        s.parts = [brighten(x) for x in string.parts]
        return s

    string = string.replace('\033[31m', '\033[91m')
    string = string.replace('\033[32m', '\033[92m')
    string = string.replace('\033[33m', '\033[93m')
    string = string.replace('\033[34m', '\033[94m')
    string = string.replace('\033[35m', '\033[95m')
    string = string.replace('\033[36m', '\033[96m')
    string = string.replace('\033[37m', '\033[97m')
    return string


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
