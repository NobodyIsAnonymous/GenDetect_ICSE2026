from integrations.gpt import get_ABI, create_gpt_chat, create_gpt_assistant
import json
import os

def test_get_ABI():
    result = get_ABI("0xBB9bc244D798123fDe783fCc1C72d3Bb8C189413")
    assert type(result) == dict
    assert type(result["result"]) == str
    assert result["status"] == "1"
    assert result["message"] == "OK"

def test_create_gpt_chat():
    assert os.getenv("OPENAI_API_KEY") is not None
    result = create_gpt_chat()
    assert result is not None
    
def test_assistant():
    assert os.getenv("OPENAI_API_KEY") is not None
    result = create_gpt_assistant()
    assert result is not None
    print(result)