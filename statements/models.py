from django.db import models

class StatementSummary(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=255)
    total_income = models.DecimalField(max_digits=12, decimal_places=2)
    total_expense = models.DecimalField(max_digits=12, decimal_places=2)
    avg_monthly_income = models.DecimalField(max_digits=12, decimal_places=2)
    avg_monthly_expense = models.DecimalField(max_digits=12, decimal_places=2)
    risk_flag = models.CharField(max_length=32)

    def __str__(self):
        return self.filename