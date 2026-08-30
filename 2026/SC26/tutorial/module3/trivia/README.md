# Deep Dish Trivia

A single self-contained HTML page. No build step, no dependencies, no network calls.
Open `index.html` in a browser, or serve the directory.

24 questions across 4 rounds, with a joke between each round:

1. Is this a real flux subcommand? (8)
2. Flux internals (6)
3. HPC history (5)
4. Chicago and pizza (5)

## Running it

Locally:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

On GitHub Pages, publish from this path so the board is reachable as
`https://flux-framework.github.io/Tutorials/2026/SC26/tutorial/module3/trivia/`.

<!-- TODO(sc26): confirm the Pages source and path, and shorten the URL if the repo
     serves from a different root. -->

## Running it live

Team names are editable in place, and each team has plus and minus buttons. Scores live
in the browser tab only, so do not refresh mid-game. The round pills at the top let you
jump around if you run short on time.

Click an answer to lock it in and reveal the explanation. Jokes have a "Tell it" button
so the punchline stays hidden until you want it.

## Editing questions

Everything is in the `ROUNDS` array near the top of the `<script>` block. Each item is
`{ q, opts, a, why }` where `a` is the zero-based index of the correct option.

Answers in round 1 were checked against the
[flux-core man page index](https://flux-framework.readthedocs.io/projects/flux-core/en/latest/man1/index.html).
If you add questions there, check them the same way rather than guessing, since the whole
joke of the round is that the real commands sound fake.
