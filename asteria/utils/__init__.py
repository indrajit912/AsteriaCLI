"""
Utils package for AsteriaCLI.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

from asteria.utils.console import (
    console,
    err_console,
    print_banner,
    print_error,
    print_info,
    print_key_value,
    print_no_results,
    print_panel,
    print_section,
    print_success,
    print_warning,
    make_table,
    make_spinner,
    make_progress_bar,
    truncate,
    confirm_action,
    prompt_input,
)
from asteria.utils.formatting import (
    format_datetime,
    format_tags,
    parse_tags,
    records_to_json,
    records_to_csv,
    short_id,
    write_export_file,
    pluralise,
)
from asteria.utils.fuzzy import (
    fuzzy_filter,
    fuzzy_search_dicts,
    exact_or_fuzzy_match,
    fuzzy_score,
)

__all__ = [
    # console
    "console",
    "err_console",
    "print_banner",
    "print_error",
    "print_info",
    "print_key_value",
    "print_no_results",
    "print_panel",
    "print_section",
    "print_success",
    "print_warning",
    "make_table",
    "make_spinner",
    "make_progress_bar",
    "truncate",
    "confirm_action",
    "prompt_input",
    # formatting
    "format_datetime",
    "format_tags",
    "parse_tags",
    "records_to_json",
    "records_to_csv",
    "short_id",
    "write_export_file",
    "pluralise",
    # fuzzy
    "fuzzy_filter",
    "fuzzy_search_dicts",
    "exact_or_fuzzy_match",
    "fuzzy_score",
]
