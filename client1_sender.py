#!/usr/bin/env python3

import socket
import sys

def text_to_binary(text):
    return ''.join(format(ord(c), '08b') for c in text)

def binary_to_text(binary):
    chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
    return ''.join(chr(int(c, 2)) for c in chars if len(c) == 8)

def calculate_parity(text):
    binary = text_to_binary(text)
    ones_count = binary.count('1')
    parity_bit = '1' if ones_count % 2 != 0 else '0'
    return parity_bit

def calculate_2d_parity(text):
    binary = text_to_binary(text)
    
    cols = 8
    rows = (len(binary) + cols - 1) // cols
    
    padded_binary = binary.ljust(rows * cols, '0')
    
    matrix = []
    for i in range(rows):
        row = list(padded_binary[i*cols:(i+1)*cols])
        matrix.append(row)
    
    row_parities = []
    for row in matrix:
        ones = sum(int(b) for b in row)
        row_parities.append('1' if ones % 2 != 0 else '0')
    
    col_parities = []
    for j in range(cols):
        ones = sum(int(matrix[i][j]) for i in range(rows))
        col_parities.append('1' if ones % 2 != 0 else '0')
    
    control_info = ''.join(row_parities) + ''.join(col_parities)
    return format(int(control_info, 2), 'X').zfill(4) if control_info else '0'

def calculate_crc16(text):
    data = text.encode('utf-8')
    crc = 0xFFFF
    polynomial = 0x1021
    
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ polynomial
            else:
                crc <<= 1
            crc &= 0xFFFF
    
    return format(crc, '04X')

def calculate_hamming(text):
    binary = text_to_binary(text)
    
    blocks = [binary[i:i+4] for i in range(0, len(binary), 4)]
    
    hamming_bits = []
    for block in blocks:
        if len(block) < 4:
            block = block.ljust(4, '0')
        
        d = [int(b) for b in block]
        
        p1 = d[0] ^ d[1] ^ d[3]
        p2 = d[0] ^ d[2] ^ d[3]
        p4 = d[1] ^ d[2] ^ d[3]
        
        hamming_bits.extend([p1, p2, p4])
    
    hamming_str = ''.join(str(b) for b in hamming_bits)
    if len(hamming_str) % 4 != 0:
        hamming_str = hamming_str.ljust((len(hamming_str) // 4 + 1) * 4, '0')
    
    result = ''
    for i in range(0, len(hamming_str), 4):
        result += format(int(hamming_str[i:i+4], 2), 'X')
    
    return result if result else '0'

def calculate_checksum(text):
    data = text.encode('utf-8')
    
    if len(data) % 2 != 0:
        data += b'\x00'
    
    checksum = 0
    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i+1]
        checksum += word
        while checksum > 0xFFFF:
            checksum = (checksum & 0xFFFF) + (checksum >> 16)
    
    checksum = ~checksum & 0xFFFF
    
    return format(checksum, '04X')

def get_control_info(text, method):
    method = method.upper()
    
    if method == 'PARITY':
        return calculate_parity(text)
    elif method == '2DPARITY':
        return calculate_2d_parity(text)
    elif method == 'CRC16':
        return calculate_crc16(text)
    elif method == 'HAMMING':
        return calculate_hamming(text)
    elif method == 'CHECKSUM':
        return calculate_checksum(text)
    else:
        raise ValueError(f"Bilinmeyen yöntem: {method}")

def create_packet(data, method, control_info):
    return f"{data}|{method}|{control_info}"

def display_menu():
    print("\n" + "="*60)
    print("       CLIENT 1 - VERİ GÖNDERİCİ")
    print("="*60)
    print("\nHata Tespit Yöntemleri:")
    print("  1. PARITY      - Even Parity Bit")
    print("  2. 2DPARITY    - 2D Matrix Parity")
    print("  3. CRC16       - CRC-16 (CCITT)")
    print("  4. HAMMING     - Hamming Code")
    print("  5. CHECKSUM    - Internet Checksum")
    print("-"*60)

def main():
    SERVER_HOST = 'localhost'
    SERVER_PORT = 5000
    
    display_menu()
    
    print("\nGöndermek istediğiniz metni girin:")
    text = input("> ").strip()
    
    if not text:
        print("Hata: Boş metin gönderilemez!")
        return
    
    print("\nHata tespit yöntemini seçin (numara veya isim):")
    method_input = input("> ").strip().upper()
    
    method_map = {
        '1': 'PARITY', '2': '2DPARITY', '3': 'CRC16', '4': 'HAMMING', '5': 'CHECKSUM'
    }
    
    method = method_map.get(method_input, method_input)
    
    try:
        control_info = get_control_info(text, method)
        packet = create_packet(text, method, control_info)
        
        print("\n" + "-"*60)
        print("PAKET BİLGİLERİ:")
        print(f"  Veri          : {text}")
        print(f"  Yöntem        : {method}")
        print(f"  Kontrol Bilgisi: {control_info}")
        print(f"  Paket         : {packet}")
        print("-"*60)
        
        print(f"\nServer'a bağlanılıyor ({SERVER_HOST}:{SERVER_PORT})...")
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((SERVER_HOST, SERVER_PORT))
            print("✓ Bağlantı kuruldu!")
            
            client_socket.sendall(packet.encode('utf-8'))
            print(f"✓ Paket gönderildi: {packet}")
            
            response = client_socket.recv(1024).decode('utf-8')
            print(f"✓ Server yanıtı: {response}")
            
    except ConnectionRefusedError:
        print(f"\n✗ Hata: Server'a bağlanılamadı! Server'ın çalıştığından emin olun.")
        print(f"  Önce 'python3 server.py' komutunu çalıştırın.")
    except ValueError as e:
        print(f"\n✗ Hata: {e}")
    except Exception as e:
        print(f"\n✗ Beklenmeyen hata: {e}")

if __name__ == "__main__":
    main()
