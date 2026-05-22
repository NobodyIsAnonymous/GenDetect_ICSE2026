import re
import subprocess

def command_extract(path):
    file_path = f'{path}README.md'
    with open(file_path, 'r') as file:
        content = file.read()

    commands = re.findall(r'forge test --[^\n]*', content)
    return commands

def save_commands(commands):
    with open(f'commands_set.txt', 'a') as file:
        for command in commands:
            # append command to file
            file.write(f'{command}\n')


if __name__ == '__main__':
    for year in ['2021', '2022', '2023']:
        commands = command_extract(f'past/{year}/')
        save_commands(commands)

    commands = command_extract('')  # 2024
    save_commands(commands)
