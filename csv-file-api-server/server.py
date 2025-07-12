import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

app = FastAPI()


def get_datafile_path():
    if not os.path.exists("datafile.txt"):
        raise FileNotFoundError(
            "Data file not specified. Use --file option when starting."
        )
    with open("datafile.txt", "r") as f:
        return f.read().strip()


def load_data():
    data_path = get_datafile_path()
    ext = os.path.splitext(data_path)[-1].lower()
    if ext == ".csv":
        return pd.read_csv(data_path)
    elif ext in [".xls", ".xlsx"]:
        return pd.read_excel(data_path)
    else:
        raise ValueError("Unsupported file format")


@app.get("/")
def get_all_rows():
    df = load_data()
    return JSONResponse(content=df.to_dict(orient="records"))


@app.get("/{column_name}")
def get_column_data(column_name: str, row_id: Optional[int] = None):
    df = load_data()
    if column_name not in df.columns:
        raise HTTPException(
            status_code=404, detail=f"Column '{column_name}' not found."
        )

    if row_id is not None:
        if 0 <= row_id < len(df):
            return {column_name: df.iloc[row_id][column_name]}
        else:
            raise HTTPException(
                status_code=404, detail=f"Row ID {row_id} is out of range."
            )
    else:
        return {column_name: df[column_name].tolist()}
