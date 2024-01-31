from django.utils.timezone import now, timedelta


def add_business_days(days):
    result = now().date()
    while days > 0:
        result += timedelta(days=1)
        if result.weekday() < 5:
            days -= 1
    return result
