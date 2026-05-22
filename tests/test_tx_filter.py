from collection.tx_filter import get_internal_tx, check_address_verified, filter_internal_tx, check_address_contract, check_address_contract_and_not_verified, get_transaction_by_hash

def test_check_address_verified():
    assert check_address_verified('0xBA12222222228d8Ba445958a75a0704d566BF2C8') == True
    assert check_address_verified('0x2C1ba59D6F58433FB1EaEe7d20b26Ed83bDA51A3') == False
    
def test_check_address_contract():
    assert check_address_contract('0x2C1ba59D6F58433FB1EaEe7d20b26Ed83bDA51A3') == True
    assert check_address_contract('0xBA12222222228d8Ba445958a75a0704d566BF2C8') == True
    assert check_address_contract('0xe6157FBB2F8662D50cAC1cfAEfC45Cafc0d1Eb7a') == False

def test_check_address_contract_and_not_verified():
    assert check_address_contract_and_not_verified('0x2C1ba59D6F58433FB1EaEe7d20b26Ed83bDA51A3') == True
    assert check_address_contract_and_not_verified('0xBA12222222228d8Ba445958a75a0704d566BF2C8') == False
    assert check_address_contract_and_not_verified('0xe6157FBB2F8662D50cAC1cfAEfC45Cafc0d1Eb7a') == False
    assert check_address_contract_and_not_verified('0xf5693Bbe961F166a2fE96094d25567f7517f27B7') == False
    assert check_address_contract_and_not_verified('0x7277494b37bfe81045daa333bd319e0d33da3860') == False

def test_get_transaction_by_hash():
    assert get_transaction_by_hash('0x725f0d65340c859e0f64e72ca8260220c526c3e0ccde530004160809f6177940') == ("0x2bfb373017349820dda2da8230e6b66739be9f96", None)
    