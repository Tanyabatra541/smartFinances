import io
import csv
import numpy as np
import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import StatementSummary


# -----------------------------
# Normalization Functions
# -----------------------------

def normalize_bofa(file_bytes):
    """Normalize Bank of America CSV to a standard schema."""
    lines = file_bytes.decode("utf-8", errors="ignore").splitlines()
    start_line = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("Date,Description,Amount,Running Bal."):
            start_line = i
            break

    df = pd.read_csv(io.StringIO("\n".join(lines[start_line:])))
    df.rename(columns={"Running Bal.": "Balance"}, inplace=True)

    # Clean and standardize
    df["Amount"] = (
        df["Amount"].astype(str)
        .str.replace(",", "")
        .str.replace("$", "")
        .astype(float)
    )
    df["Balance"] = (
        df["Balance"].astype(str)
        .str.replace(",", "")
        .str.replace("$", "")
        .replace("", np.nan)
        .astype(float)
    )
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Type"] = df["Amount"].apply(lambda x: "Credit" if x > 0 else "Debit")

    return df[["Date", "Description", "Type", "Amount", "Balance"]]


def normalize_chase(file_bytes):
    """Normalize Chase CSV, even if columns are misaligned."""
    # Detect delimiter (fallback to comma)
    sample = file_bytes[:2048].decode("utf-8", errors="ignore")
    try:
        dialect = csv.Sniffer().sniff(sample)
        delim = dialect.delimiter or ","
    except csv.Error:
        delim = ","

    df = pd.read_csv(
        io.BytesIO(file_bytes),
        dtype=str,
        delimiter=delim,
        keep_default_na=False,
        skip_blank_lines=True,
        engine="python",
    )
    df.columns = [c.strip() for c in df.columns]

    # Detect and fix misaligned structure
    first_val = str(df.iloc[0, 0]).strip()
    if "/" in first_val and "MISC" in str(df.iloc[0].get("Amount", "")):
        df.columns = [
            "Posting Date", "Description", "Amount", "Type", "Balance", "Extra1", "Extra2"
        ][: len(df.columns)]

    # Rename and clean
    df.rename(columns={"Posting Date": "Date", "Transaction Date": "Date"}, inplace=True)
    if "Description" not in df.columns:
        raise ValueError("Could not find Description column in Chase CSV")

    # Clean numeric columns
    df["Amount"] = (
        df["Amount"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.replace("CR", "", regex=False)
        .str.replace("DR", "", regex=False)
        .str.strip()
    )
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")

    if "Balance" in df.columns:
        df["Balance"] = (
            df["Balance"]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("$", "", regex=False)
            .str.strip()
        )
        df["Balance"] = pd.to_numeric(df["Balance"], errors="coerce")
    else:
        df["Balance"] = np.nan

    df.dropna(subset=["Amount"], inplace=True)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Type"] = df["Amount"].apply(lambda x: "Credit" if x > 0 else "Debit")
    df["Description"] = df["Description"].astype(str).str.strip()

    return df[["Date", "Description", "Type", "Amount", "Balance"]].reset_index(drop=True)


def detect_and_normalize(file_bytes):
    """Detect bank type and normalize accordingly."""
    header = file_bytes[:2000].decode("utf-8", errors="ignore")
    if ("Posting Date" in header) or ("Transaction Date" in header):
        return normalize_chase(file_bytes), "Chase"
    elif "Running Bal." in header:
        return normalize_bofa(file_bytes), "BoFA"
    else:
        raise ValueError("Unknown bank format. Please upload a valid CSV.")


# -----------------------------
# Upload Endpoint
# -----------------------------

@csrf_exempt
def upload_statement(request):
    """Handle CSV upload, normalization, and financial analytics."""
    if request.method != "POST" or "file" not in request.FILES:
        return JsonResponse({"error": "Please upload a CSV file."}, status=400)

    try:
        f = request.FILES["file"]
        file_bytes = f.read()

        # Detect & normalize
        df, bank_name = detect_and_normalize(file_bytes)
        df = df.dropna(subset=["Amount"])

        # Compute totals
        credits = df[df["Amount"] > 0]["Amount"].sum()
        debits = df[df["Amount"] < 0]["Amount"].sum()

        total_income = float(credits)
        total_expense = float(abs(debits))

        # Monthly breakdown
        df["month"] = df["Date"].dt.to_period("M").astype(str)
        monthly_income = df[df["Amount"] > 0].groupby("month")["Amount"].sum()
        monthly_expense = df[df["Amount"] < 0].groupby("month")["Amount"].sum().abs()

        avg_income = float(monthly_income.mean()) if not monthly_income.empty else 0.0
        avg_expense = float(monthly_expense.mean()) if not monthly_expense.empty else 0.0

        # Risk flag
        if total_income == 0 and total_expense > 0:
            flag = "No Income Detected"
        elif total_expense > total_income * 1.1:
            flag = "High Risk"
        else:
            flag = "Stable"

        # Save to DB
        record = StatementSummary.objects.create(
            filename=f.name,
            total_income=total_income,
            total_expense=total_expense,
            avg_monthly_income=avg_income,
            avg_monthly_expense=avg_expense,
            risk_flag=flag,
        )

        return JsonResponse(
            {
                "bank": bank_name,
                "id": int(record.id),
                "total_income": total_income,
                "total_expense": total_expense,
                "avg_monthly_income": avg_income,
                "avg_monthly_expense": avg_expense,
                "flag": flag,
            },
            status=200,
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)