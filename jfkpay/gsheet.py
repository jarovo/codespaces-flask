import logging
import time

from jfkpay.config import GSHeetsConfig
from jfkpay.gservices import gsheet_login
from googleapiclient.discovery import build


NOT_PAYED = 'NEZAPLACENO'

def main():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    logging.basicConfig(level=logging.DEBUG)
    gservice = gsheet_login()
    gshp = GSheetPatrol(gservice)
    while True:
        gshp.update()
        time.sleep(5)


class GSheetPatrol:
    def __init__(self, gservice) -> None:
        self.sheet = gservice.spreadsheets()
    
    def update(self):
        result = (
            self.sheet.values()
            .get(spreadsheetId=GSHeetsConfig.PAYMENTS_GSHEET_ID,
                 range=GSHeetsConfig.PAYMENTS_HEADER_RANGE_NAME)
            .execute()
        )
        values = result.get("values", [])

        if not values:
            raise Exception("No data found.")
        
        header = values.pop(0)
        logging.debug(f"{header:}")
        
        state_column_idx = header.index(GSHeetsConfig.PAYMENTS_STATE_COLUMN)

        for row in values:
            logging.debug(f"{row:}")
            #row[state_column_idx] = GSHeetsConfig.PAYMENTS_STATE_NOT_PAYED