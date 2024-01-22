import gspread

gc = gspread.service_account(filename='keyKanban.json')

# print(gc)
# Open a sheet from a spreadsheet in one go
sheets = gc.open("KANBAN").sheet1
a3 = sheets.get('a3')

# Update a range of cells using the top left corner address
sheets.update('A1', [[1, 2], [3, 4]])
print(a3)

# Format the header
sheets.format('A1:B1', {'textFormat': {'bold': True}})
