from __future__ import annotations

from io import BytesIO
from typing import Sequence

import pandas as pd
from fastapi import UploadFile
from openpyxl.workbook import Workbook
from openpyxl.workbook.protection import WorkbookProtection

REQUIRED_COLUMNS = ["first_name", "last_name", "rank", "hire_date", "attestation_date"]


class ExcelImportError(Exception):
    pass


def validate_columns(columns: Sequence[str]) -> None:
    missing = [col for col in REQUIRED_COLUMNS if col not in columns]
    if missing:
        raise ExcelImportError(f"Missing columns: {', '.join(missing)}")


def read_employees_from_excel(file: UploadFile) -> pd.DataFrame:
    try:
        df = pd.read_excel(file.file, engine="openpyxl")
    finally:
        file.file.seek(0)
    validate_columns(df.columns)
    return df


def workbook_with_password(df: pd.DataFrame, password: str) -> BytesIO:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="employees")
        workbook: Workbook = writer.book
        workbook.security = WorkbookProtection(workbookPassword=password, lockStructure=True)
    output.seek(0)
    return output
