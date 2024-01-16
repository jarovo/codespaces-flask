from jfkpay.config import GSHeetsConfig

from jfkpay.gservices import gsheet_login

from googleapiclient.discovery import build


def main():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    gservice = gsheet_login()

    # Call the Sheets API
    sheet = gservice.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=GSHeetsConfig.SAMPLE_SPREADSHEET_ID,
             range=GSHeetsConfig.SAMPLE_RANGE_NAME)
        .execute()
    )
    values = result.get("values", [])

    if not values:
        print("No data found.")
        return

    print("Name, Major:")
    for row in values:
        # Print columns A and E, which correspond to indices 0 and 4.
        print(f"{row[0]}, {row[4]}")
