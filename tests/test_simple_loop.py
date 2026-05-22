from core.loop import simplify_sequence_with_loops
from core.similarity import load_data
from pipeline.encoder import read_data_frame
from ast import literal_eval

def test_simplify_sequence_with_loops():
    sequence = [
    ('GPUExploit', 'Common', 'test'), 
    ('0x16b9a82891338f9bA80E2D6970FddA79D1eb0daE', 'Common', 'swap'),
    ('0x55d398326f99059fF775485246999027B3197955', 'Common', 'transfer'),
    ('GPUExploit', 'Common', 'call'),
    ('0x10ED43C718714eb63d5aA57B78B54704E256024E', 'Common', 'fee'),
    ('0x55d398326f99059fF775485246999027B3197955', 'Common', 'transfer'),
    ('0x61373083F4dEef88ba449AD82218059781962D76', 'Common', 'swap'),
    ('0xf51CBf9F8E089Ca48e454EB79731037a405972ce', 'Common', 'transfer'),
    ('0xf51CBf9F8E089Ca48e454EB79731037a405972ce', 'Common', 'transfer'),
    ('0xg51CBf9F8E089Ca48e454EB79731037a405972ce', 'Common', 'transfer'),
    ('0x10ED43C718714eb63d5aA57B78B54704E256024E', 'Common', 'fee'),
    ('0xg51CBf9F8E089Ca48e454EB79731037a405972ce', 'Common', 'transfer'),
    ('0x10ED43C718714eb63d5aA57B78B54704E256024E', 'Common', 'fee'),
    ('0x61373083F4dEef88ba449AD82218059781962D76', 'Common', 'swap'),
    ('0x55d398326f99059fF775485246999027B3197955', 'Common', 'transfer'),
    ('0x55d398326f99059fF775485246999027B3197955', 'Common', 'transfer'),
    ('0x55d398326f99059fF775485246999027B3197955', 'Common', 'transfer'),
    ('0x55d398326f99059fF775485246999027B3197955', 'Common', 'transfer'),
    ('0x55d398326f99059fF775485246999027B3197955', 'Common', 'transfer')
    ]
    no_loop_sequence = simplify_sequence_with_loops(sequence)
    extracted_values = [(entry[1], entry[2]) for entry in no_loop_sequence]
    print(extracted_values)
    assert extracted_values == [
        ('Common', 'test'), 
        ('Common', 'swap'),
        ('Common', 'transfer'),
        ('Common', 'call'),
        ('Common', 'fee'),
        ('Common', 'transfer'),
        ('Common', 'swap'),
        ('Common', 'loop start'),
        ('Common', 'transfer'),
        ('Common', 'loop stop'),
        ('Common', 'loop start'),
        ('Common', 'transfer'),
        ('Common', 'fee'),
        ('Common', 'loop stop'),
        ('Common', 'swap'),
        ('Common', 'loop start'),
        ('Common', 'transfer'),
        ('Common', 'loop stop')
    ]
    
    sequence = [('Common', 'test'), ('Unique', 'call'), ('Unique', 'call'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive'), ('Common', 'transfer'), ('Common', 'receive')]
    no_loop_sequence = simplify_sequence_with_loops(sequence)
    
    sequence = [('Common', 'test'), ('Common', 'approve'), ('Common', 'swap'), ('Common', 'deposit'), ('Common', 'transfer'), ('Common', 'swap'), ('Common', 'transfer'), ('Cluster', 'Unique Cluster 5'), ('Cluster', 'Unique Cluster 5'), ('Cluster', 'Unique Cluster 5'), ('Cluster', 'Common Cluster 0'), ('Common', 'approve'), ('Common', 'swap'), ('Common', 'transfer'), ('Common', 'swap'), ('Common', 'transfer')]
    no_loop_sequence = simplify_sequence_with_loops(sequence)
    print(no_loop_sequence)