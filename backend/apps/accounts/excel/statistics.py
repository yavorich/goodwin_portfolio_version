from core.abs import ExcelFileCreator


class TableStatisticsExcel(ExcelFileCreator):
    fields = (
        "day_of_week_verbose",
        "created_at",
        "trading_day",
        "funds",
        "amount",
        "percent_amount",
        "percent_total_amount",
        "profitability",
        "success_fee",
        "management_fee",
        "replenishment",
        "withdrawal",
        "status",
    )
    titles = {
        "day_of_week_verbose": "Day of week",
        "created_at": "Created at",
        "trading_day": "Trading day",
        "funds": "Funds",
        "amount": "Amount",
        "percent_amount": "Percent amount",
        "percent_total_amount": "Percent total amount",
        "profitability": "Profitability",
        "success_fee": "Success fee",
        "management_fee": "Management fee",
        "replenishment": "Replenishment",
        "withdrawal": "Withdrawal",
        "status": "Status",
    }
    save_path = "statistics"
