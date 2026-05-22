from pipeline.runner import obtain_traces, parse_trace_line, parse_trace_lines, read_second_trace
import json
import os 

def test_obtain_traces():
    obtain_traces("MorphoBlue_exp")
    assert os.path.exists("./traces/MorphoBlue_exp.log")
    with open("./traces/MorphoBlue_exp.log") as f:
        result = f.read()
    assert len(result) > 0


def test_read_second_trace():
    result = read_second_trace('./traces/MorphoBlue_exp.log')
    assert type(result) == list
    assert result[0] == '[578508] MorphoBlue::testExploit()\n'
    assert result[1] == '  ├─ [10370] 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48::symbol() [staticcall]\n'

def test_parse_trace_line():
    trace_line = '  │   └─ ← [Return] '
    parsed_trace = parse_trace_line(trace_line)
    assert type(parsed_trace) == dict
    assert parsed_trace['indent_level'] == 2
    assert parsed_trace['content'] == '← [Return]'
    
    trace_line = '  ├─ [0] VM::deal(ExploitScript: [0x7FA9385bE102ac3EAc297483Dd6233D62b3e1496], 0)'
    parsed_trace = parse_trace_line(trace_line)
    assert parsed_trace['indent_level'] == 1
    
    trace_line = '  │   │   │   ├─  emit topic 0: 0xd5e969f01efe921d3f766bdebad25f0a05e3f237311f56482bf132d0326309c0'
    parsed_trace = parse_trace_line(trace_line)
    assert parsed_trace['indent_level'] == 4
    
    trace_line = '[578508] MorphoBlue::testExploit()'
    parsed_trace = parse_trace_line(trace_line)
    assert parsed_trace['indent_level'] == 0

def test_parse_trace():
    trace_lines = [
        '[20453] ExploitScript::testExploit()',
        '  ├─ [0] VM::deal(ExploitScript: [0x7FA9385bE102ac3EAc297483Dd6233D62b3e1496], 0)',
        '  │   └─ ← [Return] ',
        '  ├─ emit log_named_decimal_uint(key: "Attacker ETH Balance Before exploit", val: 0, decimals: 18)',
        '  ├─ emit log_named_decimal_uint(key: "Attacker ETH Balance After exploit", val: 0, decimals: 18)',
        '  └─ ← [Stop] '
    ]
    parsed_trace = parse_trace_lines(trace_lines)
    trace_json = json.dumps(parsed_trace, indent=4)
    trace_dict = json.loads(trace_json)
    assert type(trace_dict) == dict
    assert trace_dict['content'] == 'root'
    assert len(trace_dict['children']) == 1
    assert trace_dict['children'][0]['content'] == '[20453] ExploitScript::testExploit()'
    assert len(trace_dict['children'][0]['children']) == 4
    
def test_read_then_parse():
    obtain_traces("MorphoBlue_exp")
    trace_lines = read_second_trace('./traces/MorphoBlue_exp.log')
    parsed_trace = parse_trace_lines(trace_lines)
    assert len(parsed_trace['children']) == 1
    assert len(parsed_trace['children'][0]['children'][0]['children']) == 2
    assert len(parsed_trace['children'][0]['children'][0]['children'][0]['children']) == 1