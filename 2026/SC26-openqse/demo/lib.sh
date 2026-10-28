# Helpers shared by the demo scripts: narration, commands, and pauses.
#
#   DEMO_AUTO=1    run straight through without waiting for Enter
#   DEMO_WIDTH=N   wrap narration at N columns (default 78)

DEMO_AUTO="${DEMO_AUTO:-0}"
DEMO_WIDTH="${DEMO_WIDTH:-78}"

if [ -t 1 ]; then
    _b=$'\e[1m' _dim=$'\e[2m' _cyan=$'\e[36m' _yel=$'\e[33m' _grn=$'\e[32m' _rst=$'\e[0m'
else
    _b="" _dim="" _cyan="" _yel="" _grn="" _rst=""
fi

# A section banner.
section() {
    local line
    line="$(printf '%*s' "$DEMO_WIDTH" '' | tr ' ' '=')"
    printf '\n%s%s\n  %s\n%s%s\n\n' "$_grn$_b" "$line" "$*" "$line" "$_rst"
}

# A smaller heading inside a section.
heading() {
    printf '\n%s## %s%s\n\n' "$_b" "$*" "$_rst"
}

# Narration, wrapped.
say() {
    printf '%s\n' "$*" | fold -s -w "$DEMO_WIDTH" | sed "s/^/${_cyan}/; s/$/${_rst}/"
    echo
}

# Wait for Enter, unless running straight through.
pause() {
    [ "$DEMO_AUTO" = 1 ] && return 0
    read -r -p "${_dim}  [Enter]${_rst}" _ </dev/tty || true
}

# Show a command, wait, then run it in this shell so variables persist.
run() {
    printf '%s$ %s%s\n' "$_yel$_b" "$*" "$_rst"
    pause
    eval "$@"
    echo
}

# Run a command a few times, a little apart, to watch something change.
watch_n() {
    local times="$1" gap="$2"
    shift 2
    printf '%s$ %s%s  %s(%s times, every %ss)%s\n' "$_yel$_b" "$*" "$_rst" "$_dim" "$times" "$gap" "$_rst"
    pause
    local i
    for ((i = 1; i <= times; i++)); do
        eval "$@"
        [ "$i" -lt "$times" ] && sleep "$gap" && echo "${_dim}  ...${_rst}"
    done
    echo
}

# Cancel everything and wait until the queue is idle, quietly.
fresh() {
    flux cancel --all --user=all >/dev/null 2>&1 || true
    flux queue idle --timeout=60 >/dev/null 2>&1 || true
    flux job purge --force --num-limit=0 >/dev/null 2>&1 || true
}
