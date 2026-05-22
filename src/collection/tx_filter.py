import requests
from dune_client.types import QueryParameter
from dune_client.client import DuneClient
from dune_client.query import QueryBase

chainid = 1
apikey = 'XT28VFFFF8CFYISGIZ57V6Y1IR85UW8VUX'

def get_internal_tx(contract_address, page, startblock):
    address = contract_address
    endblock = 	21416331
    offset = 100
    sort = 'asc'
    api = f"https://api.etherscan.io/v2/api?chainid={chainid}&module=account&action=txlistinternal" \
            f"&address={address}&startblock={startblock}&endblock={endblock}" \
            f"&page={page}&offset={offset}&sort=asc&apikey={apikey}"

    response = requests.get(api, headers={})
    # try to get the json response
    try:
        api_result = response.json()
        # if response['message'] != 'OK':
        #     return None
        return api_result
    except:
        print(f"Error: {response}")
        return None

# def check_from_address(address_from):


def check_address_contract(address):
    api = f"https://api.etherscan.io/api"\
            f"?module=proxy"\
            f"&action=eth_getCode"\
            f"&address={address}"\
            f"&tag=latest"\
            f"&apikey={apikey}"

    response = requests.get(api, headers={})
    try:
        response = response.json()
        if response['result'] == '0x':
            return False
        else:
            return True
    except:
        print(f"Error: {response}")
        return None

def check_address_verified(address_to):
    api = f"https://api.etherscan.io/v2/api"\
        f"?chainid={chainid}"\
        f"&module=contract"\
        f"&action=getabi"\
        f"&address={address_to}"\
        f"&apikey={apikey}"\

    response = requests.get(api, headers={})
    try :
        response = response.json()
        if response['message'] == "NOTOK":
            return False
        if response['message'] == "OK":
            return True
    except:
        print(f"Error: {response}")
        return None

def check_address_contract_and_not_verified(address):
    is_contract = check_address_contract(address)
    is_verified = check_address_verified(address)
    if is_contract and not is_verified:
        return True
    else:
        return False

def filter_internal_tx(json_reponse):
    result = api_result['result']
    for internal_tx in result:
        print(internal_tx['from'], internal_tx['to'], internal_tx['value'])

def get_tx_from(tx_hash):
    pass

def get_tx_to(tx_hash):
    pass

def get_transaction_by_hash(tx_hash):
    url = f"https://api.etherscan.io/api?module=proxy&action=eth_getTransactionByHash&txhash={tx_hash}&apikey={apikey}"
    response = requests.get(url)
    data = response.json()

    if 'result' in data and data['result']:
        tx_data = data['result']
        sender = tx_data['from']
        receiver = tx_data.get('to', 'Contract Creation')  # 如果 to 为空，表示合约创建
        value = int(tx_data['value'], 16) / 1e18  # 转换为 ETH
        return sender, receiver
    else:
        return None

def ethereum_filter():
    page = 1
    startblock = 10252930
    visited = set() # set of visited addresses

    while (response := get_internal_tx('0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D', page, startblock)) is not None:
        if page == 99:
            startblock = response['result'][-1]['blockNumber']
            page = 1
        for internal_tx in response['result']:
            print('blockNumber: '+str(internal_tx['blockNumber'])+f', page: {page}, visited lengtgh: ' + str(len(visited)))
            parent_tx_hash = internal_tx['hash']
            parent_tx_from, parent_tx_to = get_transaction_by_hash(parent_tx_hash) #主要是这个慢

            if parent_tx_to not in visited:
                visited.add(parent_tx_to)
                # if parent_tx_to != None and check_address_contract_and_not_verified(parent_tx_to):
                if parent_tx_to != None and check_address_contract(parent_tx_to) and not check_address_verified(parent_tx_to):
                    with open('sus_internal_tx.csv', 'a') as f:
                        f.write(f"{parent_tx_hash}, {parent_tx_from}, {parent_tx_to}, {internal_tx['value']}\n")
                        print(f"Found suspicious tx: {parent_tx_from} -> {parent_tx_to} with value {internal_tx['value']}")
                elif parent_tx_to == None and parent_tx_from != None:
                    with open('sus_internal_tx.csv', 'a') as f:
                        f.write(f"{parent_tx_hash}, {parent_tx_from}, {parent_tx_to}, {internal_tx['value']}\n")
                        print(f"Found suspicious tx: {parent_tx_from} -> {parent_tx_to} with value {internal_tx['value']}")
                else:
                    print("new normal transaction")
            else:
                print(f"Already visited {parent_tx_from} -> {parent_tx_to}")

        page += 1

    with open('visited_addresses.txt', 'w') as f:
        for address in visited:
            f.write(f"{address}\n")
    print("Finished")

def dune_filter():

    dune = DuneClient(
        api_key='kAzbjfgjX3FTIfaQRE8PJovjG4HODTWs',
        base_url="https://api.dune.com",
        request_timeout=600 # request will time out after 300 seconds
    )
    query = QueryBase(
        name="tx filter",
        query_id=4477366,
        params=[
            # QueryParameter.number_type(name="latest_block_number", value=latest_block_number),
            QueryParameter.text_type(name="creation_gap", value="30"),
            QueryParameter.text_type(name="final_date", value="2023-01-01 00:00"),
            QueryParameter.text_type(name="first_date", value="2022-01-01 00:00"),
        ],
    )
    print("Results available at", query.url())
    results_df = dune.run_query_dataframe(query)

    results_df.to_csv(f"dune_results_2023.csv")


if __name__ == '__main__':
    # ethereum_filter()
    for i in range(1):
        latest_block_number = dune_filter()
        # dune_filter(latest_block_number)
