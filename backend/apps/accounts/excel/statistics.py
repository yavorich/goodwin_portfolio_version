from core.abs import ExcelFileCreator


# class VDHistoryExcel(ExcelFileCreator):
#     fields = (
#         "date",
#         "user",
#         "is_decrease_request_number",
#         "vin",
#         "color",
#         *MANUAL_SEARCH_PARAMETERS,
#     )
#     titles = EXCEL_TITLES
#     save_path = "history/VD"


class TableStatisticsExcel(ExcelFileCreator):
    fields = ""
    titles = {}
    save_path = "statistics"
