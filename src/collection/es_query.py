import time
from opensearchpy import OpenSearch
from opensearch_dsl import Search, Document, Text, Keyword
import os
import json
import logging
import multiprocessing
import pandas as pd

class ESQuery:
    def __init__(self, tx_hash, hash_to_signature, rate_limit=1, time_window=5):
        host = '127.0.0.1'
        port = 9999
        auth = (os.getenv('OPENSEARCH_USER'), os.getenv('OPENSEARCH_PASSWORD'))  # For testing only. Don't store credentials in code.
        ca_certs_path = 'root-ca.pem'
        self.index_name = 'eth_block'

        if type(tx_hash) == str:
            self.tx_hash = [tx_hash]
        else:
            self.tx_hash = tx_hash
        self.dsl_query = {
                        "_source": False,
                        "query": {
                            "bool": {  # 使用 bool 将两个条件结合
                                "filter": [
                                    {
                                        "nested": {  # 嵌套查询必须是独立的
                                            "inner_hits": {
                                                "_source": [
                                                    "Transactions.Hash",
                                                    "Transactions.InternalTxns.Type",
                                                    "Transactions.InternalTxns.CallFunction",
                                                    "Transactions.InternalTxns.ToAddress",
                                                    "Transactions.InternalTxns.CallParameter"
                                                ],
                                                "size": 100
                                            },
                                            "path": "Transactions",
                                            "query": {
                                                "bool": {
                                                    "filter": [
                                                        {
                                                            "terms": {
                                                                "Transactions.Hash": self.tx_hash
                                                            }
                                                        }
                                                    ]
                                                }
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    }
        self.client = OpenSearch(
            hosts=[{'host': host, 'port': port}],
            http_compress=True,  # enables gzip compression for request bodies
            http_auth=auth,
            use_ssl=False,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
            # ca_certs=ca_certs_path
        )
        self.hash_to_signature = hash_to_signature
        self.response = self._query_internal_txns()
        self.length = len(self.response['hits']['hits'])

    def _query_internal_txns(self):
        response = self.client.search(index=self.index_name, body=self.dsl_query, timeout=300)
        return response

    def batch_get_internal_txns(self):
        batch_internal_txns = []
        for hit in self.response['hits']['hits']:
            batch_internal_txns.append(hit['inner_hits']['Transactions']['hits']['hits'][0]['_source']['InternalTxns'])
        return batch_internal_txns

    def append_vector_to_csv(self, csv_file):
        df_list = []

        for i in range(self.length):
            call_types, function_calls, contract_addresses, contract_params = self.get_trace_vector_by_index(i)
            function_names = self.get_decoded_function_calls_by_index(function_calls)
            transaction_hash = self.response['hits']['hits'][i]['inner_hits']['Transactions']['hits']['hits'][0]['_source']['Hash']

            df_list.append({
                'TransactionHash': transaction_hash,
                'CallTypes': call_types,
                'FunctionNames': function_names,
                'ContractAddresses': contract_addresses,
                'ContractParams': contract_params
            })

        df = pd.DataFrame(df_list)
        df.set_index('TransactionHash', inplace=True)
        df.to_csv(csv_file, mode='a', header=not os.path.exists(csv_file))

    def get_trace_vector_by_index(self, index):
        batch_internal_txns = self.batch_get_internal_txns()
        call_types = []
        function_calls = []
        contract_addresses = []
        contract_params = []
        for internal_txn in batch_internal_txns[index]:
            call_types.append(internal_txn['Type'])
            function_calls.append(internal_txn['CallFunction'])
            contract_addresses.append(internal_txn['ToAddress'])
            contract_params.append(internal_txn['CallParameter'])
        return call_types, function_calls, contract_addresses, contract_params

    def _query_trace_vector(self):
        response = self.client.search(index=self.index_name, body=self.dsl_query)
        internal_txns = response['hits']['hits'][0]['inner_hits']['Transactions']['hits']['hits'][0]['_source']['InternalTxns']

        function_calls = []
        contract_addresses = []
        contract_params = []
        call_types = []
        for internal_txn in internal_txns:
            function_calls.append(internal_txn['CallFunction'])
            contract_addresses.append(internal_txn['ToAddress'])
            contract_params.append(internal_txn['CallParameter'])
            call_types.append(internal_txn['Type'])

        return call_types, function_calls, contract_addresses, contract_params

    def get_decoded_function_calls_by_index(self, function_calls):
        decoded_function_calls = []
        for function_call in function_calls:
            decoded_function_calls.append(self.hash_to_signature.get(function_call, 'Unknown'))

        function_names = []
        for decoded_function_call in decoded_function_calls:
            function_names.append(decoded_function_call.split('(')[0])

        return function_names
