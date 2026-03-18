"""Dependency-free interactive widgets for CLI host bridges."""

from __future__ import annotations

from contextlib import contextmanager
import os
import select
import sys
from typing import Any, Callable, Iterable, Mapping, Protocol, TextIO

if os.name == "nt":  # pragma: no cover - Windows path is exercised only on Windows.
    import msvcrt
else:  # pragma: no cover - POSIX path is exercised only on POSIX.
    import termios
    import tty

CLI_RENDERER_AUTO = "auto"
CLI_RENDERER_INTERACTIVE = "interactive"
CLI_RENDERER_TEXT = "text"
CLI_RENDERER_INQUIRER_ALIAS = "inquirer"

_KEY_UP = "up"
_KEY_DOWN = "down"
_KEY_LEFT = "left"
_KEY_RIGHT = "right"
_KEY_ENTER = "enter"
_KEY_SPACE = "space"
_KEY_CANCEL = "cancel"


class CliInteractiveError(RuntimeError):
    """Raised when the built-in terminal interaction cannot continue safely."""


class CliInteractiveSession(Protocol):
    """Minimal protocol used by runtime bridge tests and helper scripts."""

    def is_available(self) -> bool:
        """Return True when the session can render an interactive form."""

    def select(
        self,
        *,
        title: str,
        items: Iterable[Mapping[str, Any]],
        instructions: str,
        initial_value: Any | None = None,
    ) -> Any:
        """Collect a single choice."""

    def multi_select(
        self,
        *,
        title: str,
        items: Iterable[Mapping[str, Any]],
        instructions: str,
        initial_values: Iterable[Any] = (),
        required: bool = False,
    ) -> list[Any]:
        """Collect multiple choices."""

    def confirm(
        self,
        *,
        title: str,
        yes_label: str,
        no_label: str,
        default_value: bool | None = None,
        instructions: str,
    ) -> bool:
        """Collect a boolean confirmation."""


InteractiveSessionFactory = Callable[[], CliInteractiveSession | None]


def normalize_cli_renderer(renderer: str) -> str:
    """Normalize public CLI renderer names into the internal bridge modes."""
    normalized = (renderer or "").strip().casefold() or CLI_RENDERER_AUTO
    aliases = {
        CLI_RENDERER_AUTO: CLI_RENDERER_AUTO,
        CLI_RENDERER_INTERACTIVE: CLI_RENDERER_INTERACTIVE,
        CLI_RENDERER_TEXT: CLI_RENDERER_TEXT,
        CLI_RENDERER_INQUIRER_ALIAS: CLI_RENDERER_INTERACTIVE,
    }
    if normalized not in aliases:
        raise CliInteractiveError(f"Unsupported CLI renderer: {renderer}")
    return aliases[normalized]


def resolve_cli_renderer(
    *,
    renderer: str,
    session_factory: InteractiveSessionFactory | None = None,
) -> tuple[str, CliInteractiveSession | None]:
    """Pick the effective CLI renderer and optionally create an interactive session."""
    requested = normalize_cli_renderer(renderer)
    if requested == CLI_RENDERER_TEXT:
        return CLI_RENDERER_TEXT, None

    session = session_factory() if session_factory is not None else TerminalInteractiveSession()
    if session is not None and session.is_available():
        return CLI_RENDERER_INTERACTIVE, session
    if requested == CLI_RENDERER_INTERACTIVE:
        return CLI_RENDERER_TEXT, None
    return CLI_RENDERER_TEXT, None


class TerminalInteractiveSession:
    """Small interactive terminal menu used by CLI bridges when TTY is available."""

    def __init__(self, *, input_stream: TextIO | None = None, output_stream: TextIO | None = None) -> None:
        self.input_stream = input_stream or sys.stdin
        self.output_stream = output_stream or sys.stdout
        self._rendered_lines = 0

    def is_available(self) -> bool:
        return bool(
            hasattr(self.input_stream, "isatty")
            and hasattr(self.output_stream, "isatty")
            and self.input_stream.isatty()
            and self.output_stream.isatty()
        )

    def select(
        self,
        *,
        title: str,
        items: Iterable[Mapping[str, Any]],
        instructions: str,
        initial_value: Any | None = None,
    ) -> Any:
        options = tuple(items)
        if not options:
            raise CliInteractiveError("Interactive select requires at least one option")

        current_index = self._resolve_initial_index(options, initial_value=initial_value)
        with self._terminal_control():
            while True:
                self._render_menu(
                    title=title,
                    instructions=instructions,
                    options=options,
                    current_index=current_index,
                )
                key = self._read_key()
                if key == _KEY_UP:
                    current_index = (current_index - 1) % len(options)
                    continue
                if key == _KEY_DOWN:
                    current_index = (current_index + 1) % len(options)
                    continue
                if key == _KEY_ENTER:
                    selection = options[current_index]
                    self._finish_prompt(f"{title}: {selection.get('label') or selection.get('value')}")
                    return selection.get("value")
                if key.isdigit():
                    digit_index = int(key) - 1
                    if 0 <= digit_index < len(options):
                        selection = options[digit_index]
                        self._finish_prompt(f"{title}: {selection.get('label') or selection.get('value')}")
                        return selection.get("value")

    def multi_select(
        self,
        *,
        title: str,
        items: Iterable[Mapping[str, Any]],
        instructions: str,
        initial_values: Iterable[Any] = (),
        required: bool = False,
    ) -> list[Any]:
        options = tuple(items)
        if not options:
            raise CliInteractiveError("Interactive multi-select requires at least one option")

        current_index = self._resolve_initial_index(options, initial_value=None)
        selected_values = {value for value in initial_values}
        validation_error = ""
        with self._terminal_control():
            while True:
                self._render_menu(
                    title=title,
                    instructions=instructions,
                    options=options,
                    current_index=current_index,
                    selected_values=selected_values,
                    validation_error=validation_error,
                )
                key = self._read_key()
                validation_error = ""
                if key == _KEY_UP:
                    current_index = (current_index - 1) % len(options)
                    continue
                if key == _KEY_DOWN:
                    current_index = (current_index + 1) % len(options)
                    continue
                if key == _KEY_SPACE:
                    value = options[current_index].get("value")
                    if value in selected_values:
                        selected_values.remove(value)
                    else:
                        selected_values.add(value)
                    continue
                if key == _KEY_ENTER:
                    if required and not selected_values:
                        validation_error = "At least one option is required."
                        continue
                    chosen = [
                        option.get("value")
                        for option in options
                        if option.get("value") in selected_values
                    ]
                    summary = ", ".join(
                        str(option.get("label") or option.get("value"))
                        for option in options
                        if option.get("value") in selected_values
                    ) or "(none)"
                    self._finish_prompt(f"{title}: {summary}")
                    return chosen
                if key.isdigit():
                    digit_index = int(key) - 1
                    if 0 <= digit_index < len(options):
                        value = options[digit_index].get("value")
                        if value in selected_values:
                            selected_values.remove(value)
                        else:
                            selected_values.add(value)

    def confirm(
        self,
        *,
        title: str,
        yes_label: str,
        no_label: str,
        default_value: bool | None = None,
        instructions: str,
    ) -> bool:
        default_index = 0 if default_value is not False else 1
        current_index = default_index
        options = (
            {"value": True, "label": yes_label},
            {"value": False, "label": no_label},
        )
        with self._terminal_control():
            while True:
                self._render_menu(
                    title=title,
                    instructions=instructions,
                    options=options,
                    current_index=current_index,
                )
                key = self._read_key()
                if key in {_KEY_UP, _KEY_LEFT}:
                    current_index = 0
                    continue
                if key in {_KEY_DOWN, _KEY_RIGHT}:
                    current_index = 1
                    continue
                if key == _KEY_ENTER:
                    selection = bool(options[current_index]["value"])
                    chosen_label = yes_label if selection else no_label
                    self._finish_prompt(f"{title}: {chosen_label}")
                    return selection
                if key.casefold() == "y":
                    self._finish_prompt(f"{title}: {yes_label}")
                    return True
                if key.casefold() == "n":
                    self._finish_prompt(f"{title}: {no_label}")
                    return False

    @contextmanager
    def _terminal_control(self):
        if not self.is_available():
            raise CliInteractiveError("Interactive CLI renderer requires a TTY")
        if os.name == "nt":  # pragma: no branch - chosen once per platform.
            try:
                yield
            finally:
                self._clear_rendered_block()
        else:  # pragma: no branch - chosen once per platform.
            file_descriptor = self.input_stream.fileno()
            original_state = termios.tcgetattr(file_descriptor)
            tty.setraw(file_descriptor)
            try:
                yield
            finally:
                termios.tcsetattr(file_descriptor, termios.TCSADRAIN, original_state)
                self._clear_rendered_block()

    def _render_menu(
        self,
        *,
        title: str,
        instructions: str,
        options: tuple[Mapping[str, Any], ...],
        current_index: int,
        selected_values: set[Any] | None = None,
        validation_error: str = "",
    ) -> None:
        current = options[current_index]
        lines = [title, instructions]
        for index, option in enumerate(options, start=1):
            active = index - 1 == current_index
            current_marker = ">" if active else " "
            selected_marker = ""
            if selected_values is not None:
                selected_marker = "[x] " if option.get("value") in selected_values else "[ ] "
            recommended_suffix = " (recommended)" if option.get("recommended") else ""
            lines.append(f"{current_marker} {index}. {selected_marker}{option.get('label')}{recommended_suffix}")
        detail = str(current.get("detail") or "").strip()
        description = str(current.get("description") or "").strip()
        if detail:
            lines.append(f"  {detail}")
        if description:
            lines.append(f"  {description}")
        tradeoffs = current.get("tradeoffs")
        if isinstance(tradeoffs, list):
            for tradeoff in tradeoffs[:2]:
                lines.append(f"  - {tradeoff}")
        if validation_error:
            lines.append(f"  {validation_error}")
        self._render_lines(lines)

    def _render_lines(self, lines: list[str]) -> None:
        self._clear_rendered_block()
        for line in lines:
            self.output_stream.write(f"\r\x1b[2K{line}\n")
        self.output_stream.flush()
        self._rendered_lines = len(lines)

    def _finish_prompt(self, summary: str) -> None:
        self._clear_rendered_block()
        self.output_stream.write(f"\r\x1b[2K{summary}\n")
        self.output_stream.flush()

    def _clear_rendered_block(self) -> None:
        while self._rendered_lines > 0:
            self.output_stream.write("\r\x1b[1A\x1b[2K")
            self._rendered_lines -= 1
        self.output_stream.flush()

    def _read_key(self) -> str:
        if os.name == "nt":  # pragma: no branch - chosen once per platform.
            return self._read_key_windows()
        return self._read_key_posix()

    def _read_key_windows(self) -> str:  # pragma: no cover - Windows only.
        char = msvcrt.getwch()
        if char in {"\x00", "\xe0"}:
            control = msvcrt.getwch()
            return {
                "H": _KEY_UP,
                "P": _KEY_DOWN,
                "K": _KEY_LEFT,
                "M": _KEY_RIGHT,
            }.get(control, control)
        if char == "\r":
            return _KEY_ENTER
        if char == " ":
            return _KEY_SPACE
        if char in {"\x03", "\x1b"}:
            raise CliInteractiveError("Interactive CLI prompt was cancelled")
        return char

    def _read_key_posix(self) -> str:  # pragma: no cover - POSIX only.
        char = self.input_stream.read(1)
        if char in {"\r", "\n"}:
            return _KEY_ENTER
        if char == " ":
            return _KEY_SPACE
        if char == "\x03":
            raise CliInteractiveError("Interactive CLI prompt was cancelled")
        if char == "\x1b":
            if self._has_pending_input():
                second = self.input_stream.read(1)
                if second == "[" and self._has_pending_input():
                    third = self.input_stream.read(1)
                    return {
                        "A": _KEY_UP,
                        "B": _KEY_DOWN,
                        "C": _KEY_RIGHT,
                        "D": _KEY_LEFT,
                    }.get(third, _KEY_CANCEL)
            raise CliInteractiveError("Interactive CLI prompt was cancelled")
        return char

    def _has_pending_input(self) -> bool:
        readable, _, _ = select.select([self.input_stream], [], [], 0.01)
        return bool(readable)

    @staticmethod
    def _resolve_initial_index(options: tuple[Mapping[str, Any], ...], *, initial_value: Any | None) -> int:
        if initial_value is None:
            return 0
        for index, option in enumerate(options):
            if option.get("value") == initial_value:
                return index
        return 0


__all__ = [
    "CLI_RENDERER_AUTO",
    "CLI_RENDERER_INTERACTIVE",
    "CLI_RENDERER_TEXT",
    "CliInteractiveError",
    "CliInteractiveSession",
    "InteractiveSessionFactory",
    "TerminalInteractiveSession",
    "normalize_cli_renderer",
    "resolve_cli_renderer",
]
