#!/usr/bin/env python3

import socket
import threading
import sys

def text_to_binary(text):
    return ''.join(format(ord(c), '08b') for c in text)

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

def verify_packet(packet):
    try:
        parts = packet.split('|')
        if len(parts) != 3:
            return None, "Geçersiz paket formatı"
        
        data, method, received_control = parts
        
        computed_control = get_control_info(data, method)
        
        is_valid = (received_control == computed_control)
        
        return {
            'data': data,
            'method': method,
            'received_control': received_control,
            'computed_control': computed_control,
            'is_valid': is_valid
        }, None
        
    except Exception as e:
        return None, str(e)

def display_result(result):
    print("\n" + "="*60)
    print("       VERİ DOĞRULAMA SONUCU")
    print("="*60)
    print(f"  Alınan Veri      : {result['data']}")
    print(f"  Yöntem           : {result['method']}")
    print(f"  Gelen Kontrol    : {result['received_control']}")
    print(f"  Hesaplanan Kontrol: {result['computed_control']}")
    print("-"*60)
    
    if result['is_valid']:
        print("  ✓ Status         : DATA CORRECT")
        print("    Veri başarıyla doğrulandı - Hata tespit edilmedi.")
    else:
        print("  ✗ Status         : DATA CORRUPTED")
        print("    Veri bozulmuş - Hata tespit edildi!")
    
    print("="*60)

class Client2Receiver:
    def __init__(self, host='localhost', port=5001):
        self.host = host
        self.port = port
        self.running = True
        self.packets_received = 0
        self.packets_corrupted = 0
        self.packets_valid = 0
    
    def display_header(self):
        print("\n" + "="*60)
        print("       CLIENT 2 - ALICI + HATA KONTROLCÜSÜ")
        print("="*60)
        print(f"\nDinleme: {self.host}:{self.port}")
        print("Server'dan paket bekleniyor...")
        print("Çıkış için 'q' yazın veya Ctrl+C basın")
        print("-"*60)
    
    def display_stats(self):
        print("\n" + "-"*60)
        print("İSTATİSTİKLER:")
        print(f"  Toplam Paket    : {self.packets_received}")
        print(f"  Doğru Paket     : {self.packets_valid}")
        print(f"  Bozuk Paket     : {self.packets_corrupted}")
        if self.packets_received > 0:
            error_rate = (self.packets_corrupted / self.packets_received) * 100
            print(f"  Hata Oranı      : {error_rate:.1f}%")
        print("-"*60)
    
    def handle_connection(self, client_socket, address):
        try:
            packet = client_socket.recv(4096).decode('utf-8')
            
            if packet:
                self.packets_received += 1
                print(f"\n[{self.packets_received}] Paket alındı: {packet}")
                
                result, error = verify_packet(packet)
                
                if error:
                    print(f"  ✗ Doğrulama hatası: {error}")
                else:
                    if result['is_valid']:
                        self.packets_valid += 1
                    else:
                        self.packets_corrupted += 1
                    
                    display_result(result)
                
        except Exception as e:
            print(f"  ✗ Bağlantı hatası: {e}")
        finally:
            client_socket.close()
    
    def input_handler(self):
        while self.running:
            try:
                user_input = input().strip().lower()
                if user_input == 'q':
                    print("\nClient 2 kapatılıyor...")
                    self.running = False
                    break
                elif user_input == 's':
                    self.display_stats()
            except EOFError:
                break
    
    def start(self):
        self.display_header()
        
        input_thread = threading.Thread(target=self.input_handler, daemon=True)
        input_thread.start()
        
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        server_socket.settimeout(1.0)
        
        print(f"✓ Client 2 dinlemede: {self.host}:{self.port}")
        
        try:
            while self.running:
                try:
                    client_socket, address = server_socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_connection,
                        args=(client_socket, address)
                    )
                    client_thread.start()
                except socket.timeout:
                    continue
        except KeyboardInterrupt:
            print("\n\nClient 2 kapatılıyor (Ctrl+C)...")
        finally:
            self.display_stats()
            server_socket.close()
            print("Client 2 kapatıldı.")

def main():
    receiver = Client2Receiver(host='localhost', port=5001)
    receiver.start()

if __name__ == "__main__":
    main()
