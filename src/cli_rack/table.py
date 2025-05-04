#    CLI Rack - Lightweight set of tools for building pretty-looking CLI applications in Python
#    Copyright (C) 2021 Dmitry Berezovsky
#    The MIT License (MIT)
#
#    Permission is hereby granted, free of charge, to any person obtaining
#    a copy of this software and associated documentation files
#    (the "Software"), to deal in the Software without restriction,
#    including without limitation the rights to use, copy, modify, merge,
#    publish, distribute, sublicense, and/or sell copies of the Software,
#    and to permit persons to whom the Software is furnished to do so,
#    subject to the following conditions:
#
#    The above copyright notice and this permission notice shall be
#    included in all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#    SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
Table rendering module for CLI Rack.
Provides functionality to render tables in terminal using ASCII art with different styles.
"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Any, Dict
from .ansi import Seq, AnsiCodeType, stream_supports_unicode
import re


class Alignment(str, Enum):
    """Cell content alignment options"""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


@dataclass
class TableStyleConfig:
    """Configuration for table rendering style"""

    horizontal_header: str  # Character for horizontal lines in header separator
    horizontal_row: str  # Character for horizontal lines in ordinary row delimiters
    vertical_outer: str  # Character for left/right (outer) borders
    vertical_inner: str  # Character for inner cell separators
    corner_tl: str  # Character for top-left corner
    corner_tr: str  # Character for top-right corner
    corner_bl: str  # Character for bottom-left corner
    corner_br: str  # Character for bottom-right corner
    cross: str  # Character for cross intersections
    t_down: str  # Character for T-down intersections
    t_up: str  # Character for T-up intersections
    t_left: str  # Character for T-left intersections
    t_right: str  # Character for T-right intersections
    inner_cross: Optional[str] = None  # Character for row delimiter (optional)
    use_row_delimiters: bool = False  # Whether to add row delimiters between every row

    def inherit(self, **kwargs) -> "TableStyleConfig":
        """
        Create a copy of this TableStyleConfig, overriding any provided properties.
        """
        params = {field.name: getattr(self, field.name) for field in self.__dataclass_fields__.values()}
        params.update(kwargs)
        return TableStyleConfig(**params)


class TableStyle:
    """Predefined table styles"""

    PLAIN = TableStyleConfig(
        horizontal_header="=",
        horizontal_row="-",
        vertical_outer="|",
        vertical_inner="|",
        corner_tl="+",
        corner_tr="+",
        corner_bl="+",
        corner_br="+",
        cross="+",
        t_down="+",
        t_up="+",
        t_left="+",
        t_right="+",
        inner_cross="+",
        use_row_delimiters=False,
    )
    """Uses basic ASCII characters"""
    UNICODE = TableStyleConfig(
        horizontal_header="─",
        horizontal_row="─",
        vertical_outer="│",
        vertical_inner="│",
        corner_tl="┌",
        corner_tr="┐",
        corner_bl="└",
        corner_br="┘",
        cross="┼",
        t_down="┬",
        t_up="┴",
        t_left="┤",
        t_right="├",
        inner_cross="┼",
        use_row_delimiters=False,
    )
    """Uses Unicode box-drawing characters"""

    MINIMAL = TableStyleConfig(
        horizontal_header=" ",
        horizontal_row=" ",
        vertical_outer=" ",
        vertical_inner=" ",
        corner_tl=" ",
        corner_tr=" ",
        corner_bl=" ",
        corner_br=" ",
        cross=" ",
        t_down=" ",
        t_up=" ",
        t_left=" ",
        t_right=" ",
        inner_cross=" ",
        use_row_delimiters=False,
    )
    """Uses minimal characters"""

    DOUBLE = TableStyleConfig(
        horizontal_header="═",
        horizontal_row="─",
        vertical_outer="║",
        vertical_inner="│",
        corner_tl="╔",
        corner_tr="╗",
        corner_bl="╚",
        corner_br="╝",
        cross="╬",
        t_down="╦",
        t_up="╩",
        t_left="╣",
        t_right="╠",
        inner_cross="┼",
        use_row_delimiters=True,
    )
    """Uses double-line box-drawing characters"""


@dataclass
class Column:
    name: str
    id: str
    header_align: Alignment = Alignment.CENTER
    align: Alignment = Alignment.LEFT
    header_style: Optional[AnsiCodeType] = None
    style: Optional[AnsiCodeType] = None
    width: Optional[int] = None  # New: optional fixed width for this column

    def __post_init__(self):
        if self.id is None:
            self.id = self.name


class Table:
    """Class for rendering tables in terminal"""

    def __init__(
        self,
        style: Optional[TableStyleConfig] = None,
        padding: int = 1,
        border_style: Optional[AnsiCodeType] = None,
        default_header_align: Alignment = Alignment.LEFT,
        default_header_style: Optional[AnsiCodeType] = None,
        default_cell_style: Optional[AnsiCodeType] = None,
        default_cell_align: Alignment = Alignment.LEFT,
        width: Optional[int] = None,
    ):
        self.columns: List[Column] = []
        self._col_id_map: Dict[str, int] = {}
        self.rows: List[List[str]] = []
        self.padding = padding
        self.border_style = border_style
        self.style_config = style or (TableStyle.UNICODE if stream_supports_unicode() else TableStyle.PLAIN)
        self.default_header_align = default_header_align
        self.default_header_style = default_header_style
        self.default_cell_style = default_cell_style
        self.default_cell_align = default_cell_align
        self.table_width = width

    def add_column(
        self,
        name: str,
        id: Optional[str] = None,
        header_align: Alignment = Alignment.CENTER,
        align: Alignment = Alignment.LEFT,
        header_style: Optional[AnsiCodeType] = None,
        style: Optional[AnsiCodeType] = None,
        width: Optional[int] = None,  # New: optional fixed width for this column
    ):
        col = Column(
            name=name,
            id=id or name,
            header_align=header_align or self.default_header_align,
            align=align or self.default_cell_align,
            header_style=header_style or self.default_header_style,
            style=style or self.default_cell_style,
            width=width,
        )
        self._col_id_map[col.id] = len(self.columns)
        self.columns.append(col)

    def modify_column(self, id: str, **kwargs):
        idx = self._col_id_map.get(id)
        if idx is None:
            raise ValueError(f"No column with id '{id}'")
        for k, v in kwargs.items():
            if hasattr(self.columns[idx], k):
                setattr(self.columns[idx], k, v)
            else:
                raise ValueError(f"Column has no property '{k}'")

    def add_row(self, row: List[Any]) -> None:
        num_columns = len(self.columns)
        if len(row) > num_columns:
            raise ValueError(f"Row has more elements ({len(row)}) than columns ({num_columns})")
        padded_row = [str(cell) for cell in row] + [""] * (num_columns - len(row))
        self.rows.append(padded_row)

    ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[mGKHF]")

    def strip_ansi(self, text: str) -> str:
        return self.ANSI_ESCAPE_RE.sub("", text)

    def _get_column_widths(self) -> List[int]:
        # 1. Start with explicit column widths if set
        widths = [col.width if col.width is not None else len(self.strip_ansi(col.name)) for col in self.columns]
        # 2. Expand to fit content if needed
        for row in self.rows:
            for i, cell in enumerate(row):
                cell_len = max(len(self.strip_ansi(line)) for line in self._split_cell_lines(cell))
                if self.columns[i].width is None:
                    widths[i] = max(widths[i], cell_len)
        # 3. If table_width is set, adjust widths to fit
        if self.table_width is not None:
            total_border = (len(self.columns) + 1) * len(self.style_config.vertical_outer)
            total_padding = 2 * self.padding * len(self.columns)
            fixed = sum(w for w, col in zip(widths, self.columns) if col.width is not None)
            flex_cols = [i for i, col in enumerate(self.columns) if col.width is None]
            flex_count = len(flex_cols)
            content_width = self.table_width - total_border - total_padding
            if flex_count > 0:
                # Calculate available width for flexible columns
                flex_total = content_width - fixed
                if flex_total < flex_count:
                    # Not enough space, set all flex columns to 1
                    for i in flex_cols:
                        widths[i] = 1
                else:
                    base = flex_total // flex_count
                    extra = flex_total % flex_count
                    for idx, i in enumerate(flex_cols):
                        widths[i] = base + (1 if idx < extra else 0)
            # If all columns are fixed, just use their widths
        return widths

    def _align_text(self, text: str, width: int, alignment: Alignment) -> str:
        visible_len = len(self.strip_ansi(text))
        if alignment == Alignment.LEFT:
            return text + " " * (width - visible_len)
        elif alignment == Alignment.RIGHT:
            return " " * (width - visible_len) + text
        else:
            left = (width - visible_len) // 2
            right = width - visible_len - left
            return " " * left + text + " " * right

    def _render_cell(self, content: str, width: int, alignment: Alignment) -> str:
        padding = " " * self.padding
        aligned_content = self._align_text(content, width, alignment)
        return f"{padding}{aligned_content}{padding}"

    def _render_border(self, widths: List[int], left: str, middle: str, right: str, horizontal: str) -> str:
        parts = [left]
        for i, width in enumerate(widths):
            parts.append(horizontal * (width + 2 * self.padding))
            if i < len(widths) - 1:
                parts.append(middle)
        parts.append(right)
        return "".join(parts)

    def _apply_style(self, content: str, style: Optional[AnsiCodeType]) -> str:
        return Seq.style(style, content) if style else content

    def _split_cell_lines(self, cell: str) -> List[str]:
        return cell.splitlines() or [""]

    def _render_row(self, cells: List[str], widths: List[int], col_props: List[Column], is_header=False) -> str:
        split_cells = [self._split_cell_lines(cell) for cell in cells]
        row_height = max(len(lines) for lines in split_cells)
        padded_cells = [lines + [""] * (row_height - len(lines)) for lines in split_cells]
        rendered_lines = []
        for line_idx in range(row_height):
            rendered_cells = []
            for i, (cell_lines, width, col) in enumerate(zip(padded_cells, widths, col_props)):
                align = col.header_align if is_header else col.align
                style = col.header_style if is_header else col.style
                cell_content = self._render_cell(cell_lines[line_idx], width, align)
                if style:
                    cell_content = self._apply_style(cell_content, style)
                rendered_cells.append(cell_content)
            left_border = self.style_config.vertical_outer
            right_border = self.style_config.vertical_outer
            inner_border = self.style_config.vertical_inner
            if self.border_style:
                left_border = self._apply_style(left_border, self.border_style)
                right_border = self._apply_style(right_border, self.border_style)
                inner_border = self._apply_style(inner_border, self.border_style)
            rendered_lines.append(left_border + inner_border.join(rendered_cells) + right_border)
        return "\n".join(rendered_lines)

    def _render_border_line(
        self, widths: List[int], left: str, middle: str, right: str, horizontal: Optional[str] = None
    ) -> str:
        if horizontal is None:
            horizontal = self.style_config.horizontal_row
        border = self._render_border(widths, left, middle, right, horizontal)
        return self._apply_style(border, self.border_style)

    def render(self) -> str:
        if not self.rows and not self.columns:
            return ""
        widths = self._get_column_widths()
        lines = []
        # Top border
        lines.append(
            self._render_border_line(
                widths,
                self.style_config.corner_tl,
                self.style_config.t_down,
                self.style_config.corner_tr,
                self.style_config.horizontal_header,
            )
        )
        # Headers
        if self.columns:
            lines.append(self._render_row([col.name for col in self.columns], widths, self.columns, is_header=True))
            # Header separator
            lines.append(
                self._render_border_line(
                    widths,
                    self.style_config.t_right,
                    self.style_config.cross,
                    self.style_config.t_left,
                    self.style_config.horizontal_header,
                )
            )
        # Rows
        for idx, row in enumerate(self.rows):
            lines.append(self._render_row(row, widths, self.columns, is_header=False))
            if self.style_config.use_row_delimiters and idx < len(self.rows) - 1:
                left = self.style_config.t_right
                middle = self.style_config.inner_cross or self.style_config.cross
                right = self.style_config.t_left
                lines.append(self._render_border_line(widths, left, middle, right, self.style_config.horizontal_row))
        # Bottom border
        lines.append(
            self._render_border_line(
                widths,
                self.style_config.corner_bl,
                self.style_config.t_up,
                self.style_config.corner_br,
                self.style_config.horizontal_header,
            )
        )
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.render()
