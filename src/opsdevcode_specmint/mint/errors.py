"""Mint diagnostics. Expected failures are data, not host HTTP problems."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from opsdevcode_specmint.mint.ast import SourceSpan


@dataclass(frozen=True, slots=True)
class MintDiagnostic:
    code: str
    message: str
    line: int | None = None
    column: int | None = None
    unit: str | None = None
    related: tuple[SourceSpan, ...] = field(default_factory=tuple)
    end_line: int | None = None
    end_column: int | None = None
    start_offset: int | None = None
    end_offset: int | None = None
    snapshot: Mapping[str, Any] | None = None

    def render(self) -> str:
        where = ""
        if self.unit and self.line is not None and self.column is not None:
            where = f" at {self.unit}:{self.line}:{self.column}"
        elif self.line is not None and self.column is not None:
            where = f" at line {self.line} column {self.column}"
        return f"{self.code}{where}: {self.message}"


class MintError(Exception):
    def __init__(self, diagnostic: MintDiagnostic) -> None:
        self.diagnostic = diagnostic
        super().__init__(diagnostic.message)


class MintParseError(MintError):
    pass


class MintStaticError(MintError):
    pass


class MintCatalogError(MintError):
    pass


def parse_error(
    line: int,
    column: int,
    hint: str,
    *,
    unit: str | None = None,
    end_line: int | None = None,
    end_column: int | None = None,
    start_offset: int | None = None,
    end_offset: int | None = None,
) -> MintParseError:
    return MintParseError(
        MintDiagnostic(
            code="MINT_PARSE",
            message=f"Mint parse error at line {line} column {column}: {hint}",
            line=line,
            column=column,
            unit=unit,
            end_line=end_line or line,
            end_column=end_column or (column + 1),
            start_offset=start_offset,
            end_offset=end_offset,
        )
    )


def static_error(
    line: int,
    column: int,
    hint: str,
    *,
    unit: str | None = None,
    end_line: int | None = None,
    end_column: int | None = None,
    start_offset: int | None = None,
    end_offset: int | None = None,
) -> MintStaticError:
    return MintStaticError(
        MintDiagnostic(
            code="MINT_STATIC",
            message=f"Mint static error at line {line} column {column}: {hint}",
            line=line,
            column=column,
            unit=unit,
            end_line=end_line or line,
            end_column=end_column or (column + 1),
            start_offset=start_offset,
            end_offset=end_offset,
        )
    )


def coded_error(
    code: str,
    message: str,
    *,
    span: SourceSpan | None = None,
    related: tuple[SourceSpan, ...] = (),
    snapshot: Mapping[str, Any] | None = None,
    end_line: int | None = None,
    end_column: int | None = None,
    start_offset: int | None = None,
    end_offset: int | None = None,
) -> MintStaticError:
    line = span.line if span else None
    column = span.column if span else None
    unit = span.unit if span else None
    span_end_line = span.end_line if span else None
    span_end_column = span.end_column if span else None
    span_start_offset = span.start_offset if span else None
    span_end_offset = span.end_offset if span else None
    return MintStaticError(
        MintDiagnostic(
            code=code,
            message=message,
            line=line,
            column=column,
            unit=unit,
            related=related,
            end_line=end_line if end_line is not None else span_end_line,
            end_column=end_column if end_column is not None else span_end_column,
            start_offset=start_offset if start_offset is not None else span_start_offset,
            end_offset=end_offset if end_offset is not None else span_end_offset,
            snapshot=snapshot,
        )
    )


def catalog_error(message: str) -> MintCatalogError:
    return MintCatalogError(MintDiagnostic(code="MINT_CATALOG", message=message))
