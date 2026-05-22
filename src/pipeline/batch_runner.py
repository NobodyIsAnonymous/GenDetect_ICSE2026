import re
import subprocess
import config

def read_commands(start_line):
    with open('commands_set.txt', 'r') as file:
        commands = file.readlines()
    return commands[start_line:]

def extract_contract_name(command):
    # Extract the contract name from the command
    # forge test --contracts ./src/test/2021-04/Uranium_exp.sol -vvvv, only obtain Uranium_exp, the years might change, also the starting can be ./src or src
    match = re.search(r'--contracts\s+(?:\./|)src/test/\d{4}-\d{2}/([^/]+\.sol)', command)

    if match:
        # split the match with "/" and get the last element
        file_name = match.group().split("/")[-1]
        # remove the .sol extension
        contract = file_name.split(".")[0]
    else:
        # forge test --match-contract LavaLending_exp -vvvv, search for the format like this, excluding -vvvv
        match = re.search(r'(?<=--match-contract )(.*)', command)
        contract = match.group().split(" ")[0]
    return contract

def obtain_traces(command):
    # Run the transaction with Forge
    contract = extract_contract_name(command)
    forge_cmd = command[0:-1] +" --ignored-error-codes 5667" + " > traces/"+ contract + ".log"

    # try running the forge command
    try:
        subprocess.run(forge_cmd, shell=True, check=True)
        print(f"Traces saved to ./traces/{contract}.log")
        with open(f"./traces/{contract}.log") as f:
            result = f.read()
            if len(result) == 0:
                with open(str(config.ERROR_LOG), "a") as f:
                    f.write(f"Error: {contract} trace is empty\n")
    except Exception as e:
        print(f"Error running forge command: {e}")
        with open(str(config.ERROR_LOG), "a") as f:
            f.write(f"Error: {contract} failed to obtain trace with error {e}\n")

def read_error_log():
    with open(str(config.ERROR_LOG), "r") as f:
        errors = f.readlines()
    return errors

def check_if_command_failed(errors, command):
    contract = extract_contract_name(command)
    for error in errors:
        if contract in error:
            return True
    return False

if __name__ == '__main__':
    errors = read_error_log()
    commands = read_commands(0)
    for command in commands:
        if check_if_command_failed(errors, command):
            # retry the command
            print(f"ReObtaining traces for {command}")
            obtain_traces(command)
        else:
            continue

    print("All traces saved successfully!")
