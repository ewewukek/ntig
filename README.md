Interactive git log with commit preview. Inspired by [Tig](https://jonas.github.io/tig/).

Requires `termios` package and ANSI escape sequences support.

![](screenshot.png?raw=true)

```
options:
  --ntig-hash       hash color (default: yellow)
  --ntig-date       date color (default: default)
  --ntig-date-fmt   date format (default: %d %b %H:%M)
  --ntig-author     author name color (default: cyan)
  --ntig-node       graph node color (default: bright-yellow)
  --ntig-head       HEAD color (default: bright-cyan)
  --ntig-branch     local branch color (default: bright-green)
  --ntig-remote     remote branch color (default: bright-red)
  --ntig-tag        tag color (default: bright-yellow)
  --ntig-stash      stash color (default: bright-blue)
  --ntig-refs-bold  show refs in bold (default: False)
  --ntig-decorate   decorate refs (default: False)
  --ntig-log        log format (default: {hash} {date} {author} {graph} {refs}{message})
  --ntig-pager      pager to pipe output of git show (default: none)

other options will be passed to git log

  h, H              - show help
  q, Q              - exit
  arrows, pgup/pgdn - navigate
  enter             - select or close
```
