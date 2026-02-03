import re
import subprocess
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))

def command_extract(path):
    file_path = os.path.join(path, 'README.md')
    with open(file_path, 'r') as file:
        content = file.read()

    commands = re.findall(r'forge test --[^\n]*', content)
    return commands

def save_commands(commands):
    output_path = os.path.join(project_root, 'commands_set.txt')
    with open(f'commands_set.txt', 'a') as file:
        for command in commands:
            # append command to file
            file.write(f'{command}\n')
            

if __name__ == '__main__':
    past_dir = os.path.join(project_root, 'past')
    for year in ['2021', '2022', '2023']:
        year_path = os.path.join(past_dir, year)
        commands = command_extract(year_path)
        save_commands(commands)
    
    commands = command_extract('')  # 2024
    save_commands(commands)
    
