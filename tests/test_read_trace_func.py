from pipeline.parser import read_structured_trace, read_structured_traces, preorder_traversal, separate_content, create_csv_file, separate_attack_vector, preorder_traversal_ignore_static_call_children
import json
import os

def test_read_structured_trace():
    structured_trace = read_structured_trace('./structured_traces/MorphoBlue_exp.json')
    assert type(structured_trace) == dict
    assert structured_trace['content'] == 'root'
    assert len(structured_trace['children']) == 1
    assert structured_trace['children'][0]['content'] == '[578508] MorphoBlue::testExploit()'

def test_read_structured_traces():
    structured_traces = read_structured_traces('./structured_traces/', start_file='0vix_exp.json', end_file='USDs_exp.json')
    assert type(structured_traces) == list
    assert len(structured_traces) == 3
    assert structured_traces[0]['content'] == 'root'
    assert structured_traces[2]['children'][0]['content'] == '[131948] AttackerAddress::testExploit()'
    

def test_preorder_traversal():
    data = {
        "content": "root",
        "children": [
            {
                "content": "A",
                "children": [
                    {
                        "content": "B",
                        "children": []
                    },
                    {
                        "content": "C",
                        "children": []
                    }
                ]
            },
            {
                "content": "D",
                "children": [
                    {
                        "content": "E",
                        "children": []
                    },
                    {
                        "content": "F",
                        "children": [
                            {
                            "content": "g",
                            "children": []
                            },
                            {
                            "content": "h",
                            "children": []
                            }
                        ]
                    }
                ]
            }
        ]
    }
    preorder_result = preorder_traversal(data)
    assert preorder_result == ['root', 'A', 'B', 'C', 'D', 'E', 'F','g', 'h']
    data = structured_trace = read_structured_trace('./structured_traces/MorphoBlue_exp.json')
    preorder_result = preorder_traversal(data)
    assert preorder_result[0] == 'root'
    assert preorder_result[1] == '[578508] MorphoBlue::testExploit()'
    assert preorder_result[2] == '[10370] 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48::symbol() [staticcall]'
    assert preorder_result[-1] == '\u2190 [Stop]'

def test_preorder_traversal_ignore_static_call_children():
    data = {
        "content": "root",
        "children": [
            {
                "content": "A",
                "children": [
                    {
                        "content": "B",
                        "children": []
                    },
                    {
                        "content": "C",
                        "children": []
                    }
                ]
            },
            {
                "content": "D",
                "children": [
                    {
                        "content": "E",
                        "children": []
                    },
                    {
                        "content": "[10370] 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48::symbol() [staticcall]",
                        "children": [
                            {
                            "content": "g",
                            "children": []
                            },
                            {
                            "content": "h",
                            "children": []
                            }
                        ]
                    }
                ]
            }
        ]
    }
    preorder_result = preorder_traversal_ignore_static_call_children(data)
    assert preorder_result == ['root', 'A', 'B', 'C', 'D', 'E']
    data = structured_trace = read_structured_trace('./structured_traces/MorphoBlue_exp.json')
    preorder_result = preorder_traversal_ignore_static_call_children(data)
    assert preorder_result[0] == 'root'
    assert preorder_result[1] == '[578508] MorphoBlue::testExploit()'
    assert preorder_result[2] == 'emit log_named_decimal_uint(key: \"Attacker USDC Balance Before exploit\", val: 0, decimals: 6)'
    assert preorder_result[3] == '[479741] 0x9C4Fe5FFD9A9fC5678cFBd93Aa2D4FD684b67C4C::swap(132577813003136114 [1.325e17], 0, MorphoBlue: [0x7FA9385bE102ac3EAc297483Dd6233D62b3e1496], 0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000)'
    assert preorder_result[-1] == '\u2190 [Stop]'
    
def test_separate_content():
    line = '[578508] MorphoBlue::testExploit()'
    (address, function, params) = separate_content(line)
    assert address == 'MorphoBlue'
    assert function == 'testExploit'
    assert params == '()'
    line = '\u2190 [Stop]'
    (address, function, params) = separate_content(line)
    assert address == None
    assert function == None
    
    line = '[34852] 0x45804880De22913dAFE09f4980848ECE6EcbAf78::transfer(MorphoBlue: [0x7FA9385bE102ac3EAc297483Dd6233D62b3e1496], 156043732137761410 [1.56e17])'
    (address, function, params) = separate_content(line)
    assert address == '0x45804880De22913dAFE09f4980848ECE6EcbAf78'
    assert function == 'transfer'
    assert params == '(MorphoBlue:[0x7FA9385bE102ac3EAc297483Dd6233D62b3e1496],156043732137761410[1.56e17])'
    
    line = '[10370] 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48::symbol() [staticcall]'
    (address, function, params) = separate_content(line)
    assert address == '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'
    assert function == 'symbol'
    assert params == '()[staticcall]'
    
    line = '[0] 0x000097D4a261d7ad074089Ca08eFA2b136aa6d38::fallback{value: 30000000000000000}()'
    (address, function, params) = separate_content(line)
    assert address == '0x000097D4a261d7ad074089Ca08eFA2b136aa6d38'
    assert function == 'fallback'
    assert params == '{value:30000000000000000}()'
    
def test_create_csv_file():
    create_csv_file()
    assert os.path.exists('attack_vectors.csv')

def test_separate_attack_vectors():
    data = [(None, None, None), ('MorphoBlue', 'testExploit', '()'), ('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', 'symbol', '()[staticcall]'), ('0x43506849D7C04F9138D1A2050bbF3A0c054402dd', 'symbol', '()[delegatecall]'), (None, None, None), (None, None, None), ('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', 'balanceOf', '(MorphoBlue:[0x7FA9385bE102ac3EAc297483Dd6233D62b3e1496])[staticcall]'), ('0x43506849D7C04F9138D1A2050bbF3A0c054402dd', 'balanceOf', '(MorphoBlue:[0x7FA9385bE102ac3EAc297483Dd6233D62b3e1496])[delegatecall]'), (None, None, None), (None, None, None), ('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', 'decimals', '()[staticcall]'), ('0x43506849D7C04F9138D1A2050bbF3A0c054402dd', 'decimals', '()[delegatecall]'), (None, None, None)]
    result = separate_attack_vector(data)
    assert result[0] == ['MorphoBlue', '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', '0x43506849D7C04F9138D1A2050bbF3A0c054402dd', '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', '0x43506849D7C04F9138D1A2050bbF3A0c054402dd', '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', '0x43506849D7C04F9138D1A2050bbF3A0c054402dd']
    assert result[1] == ['testExploit', 'symbol', 'symbol', 'balanceOf', 'balanceOf', 'decimals', 'decimals']
    assert result[2] == ['()', '()[staticcall]', '()[delegatecall]', '(MorphoBlue:[0x7FA9385bE102ac3EAc297483Dd6233D62b3e1496])[staticcall]', '(MorphoBlue:[0x7FA9385bE102ac3EAc297483Dd6233D62b3e1496])[delegatecall]', '()[staticcall]', '()[delegatecall]']