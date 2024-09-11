Interactive git log with commit preview. Inspired by [Tig](https://jonas.github.io/tig/).

Requires `termios` package.

![](screenshot.png?raw=true)

```
options:
  --ntig-hash       hash color (default: yellow)
  --ntig-date       date color (default: default)
  --ntig-author     author name color (default: cyan)
  --ntig-node       graph node color (default: bright-yellow)
  --ntig-date-fmt   date format (default: %d %b %H:%M)
  --ntig-log        log format (default: {hash} {date} {author} {graph} {message})
  --ntig-pager      pager to pipe output of git show (default: none)

other options will be passed to git log

  h, H              - show help
  q, Q              - exit
  arrows, pgup/pgdn - navigate
  enter             - select or close
```
