from collection.commands import command_extract

def test_extract_commands():
    command_extract('')
    command_extract('past/2023/')
    command_extract('past/2022/')
    command_extract('past/2021/')