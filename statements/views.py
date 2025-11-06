import io
import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import StatementSummary

@csrf_exempt
def upload_statement(request):
    if request.method != "POST" or "file" not in request.FILES:
        return JsonResponse({"error": "Please upload a CSV file."}, status=400)

    f = request.FILES["file"]
    df = pd.read_csv(io.BytesIO(f.read()))

    # compute income/expense summary
    income = df[df["Type"].str.lower() == "credit"]["Amount"].sum()
    expense = df[df["Type"].str.lower() == "debit"]["Amount"].sum()
    avg_income = df[df["Type"].str.lower() == "credit"].groupby(df["Date"].str[:7])["Amount"].sum().mean()
    avg_expense = df[df["Type"].str.lower() == "debit"].groupby(df["Date"].str[:7])["Amount"].sum().mean()

    flag = "High Risk" if expense > income * 1.1 else "Stable"

    record = StatementSummary.objects.create(
        filename=f.name,
        total_income=float(income),
        total_expense=float(expense),
        avg_monthly_income=float(avg_income),
        avg_monthly_expense=float(avg_expense),
        risk_flag=flag,
    )

    return JsonResponse({
        "id": int(record.id),
        "total_income": float(income),
        "total_expense": float(expense),
        "avg_monthly_income": float(avg_income),
        "avg_monthly_expense": float(avg_expense),
        "flag": flag
    })