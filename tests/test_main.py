from pipeline.batch_runner import extract_contract_name, read_error_log

def test_extract_contract_name():
    command = "forge test --contracts ./src/test/2021-04/Uranium_exp.sol -vvvv"
    result = extract_contract_name(command)
    assert result == "Uranium_exp"
    
    command = "forge test --match-contract LavaLending_exp -vvvv"
    result = extract_contract_name(command)
    assert result == "LavaLending_exp"
    
    command = "forge test --contracts src/test/2021-04/Uranium_exp.sol -vvvv"
    result = extract_contract_name(command)
    assert result == "Uranium_exp"
    
    command = "forge test --match-contract LavaLending_exp -vvvv"
    result = extract_contract_name(command)
    assert result == "LavaLending_exp"
    
    command = "forge test --contracts ./src/test/2021-04/Uranium_exp.sol -vvvv"
    result = extract_contract_name(command)
    assert result == "Uranium_exp"
    
    command = "forge test --match-contract LavaLending_exp -vvvv"
    result = extract_contract_name(command)
    assert result == "LavaLending_exp"
    
    command = "forge test --contracts src/test/2021-04/Uranium_exp.sol -vvvv"
    result = extract_contract_name(command)
    assert result == "Uranium_exp"
    
    command = "forge test --match-contract LavaLending_exp -vvvv"
    result = extract_contract_name(command)
    assert result == "LavaLending_exp"
    
    command = "forge test --contracts ./src/test/2021-04/Uranium_exp.sol -vvvv"
    result = extract_contract_name(command)
    assert result == "Uranium_exp"
    
    command = "forge test --match-contract LavaLending_exp -vvvv"
    result = extract_contract_name(command)
    assert result == "LavaLending_exp"
    
    command = "forge test --contracts src/test/2021-04/Uranium_exp.sol -vvvv"
    result = extract_contract_name(command)
    assert result == "Uranium_exp"
    
    command = "forge test --match-contract LavaLending_exp -vvvv"
    result = extract_contract_name(command)
    assert result == "LavaLending_exp"
    
    command = "forge test --contracts ./src/test/2022-11/Kashi_exp.sol -vvvv"
    result = extract_contract_name(command)
    assert result == "Kashi_exp"
    
    command = "forge test --contracts ./src/test/2024-08/AAVE_Repay_Adapter.sol -vvvv"
    result = extract_contract_name(command)
    assert result == "AAVE_Repay_Adapter"
    
    
def test_read_error_log():
    result = read_error_log()
    assert len(result) == 34
    
    