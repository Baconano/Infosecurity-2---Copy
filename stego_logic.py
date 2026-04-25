from bitstring import BitArray

def embed_message(carrier_path, message_path, S, L, mode):
    # Load files as bit arrays
    P = BitArray(filename=carrier_path)
    M = BitArray(filename=message_path)
    
    # Simple check for capacit
    if S + (len(M) * L) > len(P):
        raise ValueError("Carrier file is too small for this message/periodicity.")

    # Convert P to a mutable bitarray for modification
    P_bits = list(P.bin)
    M_bits = M.bin
    
    # Embedding logic
    for i, bit in enumerate(M_bits):
        # Calculate current bit index based on S and L
        # In a real 'Mode C', L would change dynamically here
        target_index = S + (i * L)
        P_bits[target_index] = bit
        
    # Reconstruct the file
    modified_bits = BitArray(bin="".join(P_bits))
    return modified_bits

def extract_message(carrier_path, S, L, expected_length_bits):
    P = BitArray(filename=carrier_path)
    extracted_bits = []
    
    for i in range(expected_length_bits):
        target_index = S + (i * L)
        extracted_bits.append(P.bin[target_index])
        
    return BitArray(bin="".join(extracted_bits))