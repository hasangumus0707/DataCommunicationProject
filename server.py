#!/usr/bin/env python3

import socket
import threading
import random
import sys

def bit_flip(data):
    if not data:
        return data
    
    char_index = random.randint(0, len(data) - 1)
    char = data[char_index]
    
    bit_index = random.randint(0, 7)
    ascii_val = ord(char)
    corrupted_val = ascii_val ^ (1 << bit_index)
    
    if corrupted_val < 32 or corrupted_val > 126:
        corrupted_val = (corrupted_val % 95) + 32
    
    corrupted_char = chr(corrupted_val)
    
    result = data[:char_index] + corrupted_char + data[char_index+1:]
    print(f"    [Bit Flip] Karakter '{char}' → '{corrupted_char}' (pozisyon {char_index})")
    return result

def character_substitution(data):
    if not data:
        return data
    
    char_index = random.randint(0, len(data) - 1)
    original_char = data[char_index]
    
    new_char = original_char
    while new_char == original_char:
        new_char = chr(random.randint(65, 90))
    
    result = data[:char_index] + new_char + data[char_index+1:]
    print(f"    [Character Substitution] '{original_char}' → '{new_char}' (pozisyon {char_index})")
    return result

def character_deletion(data):
    if len(data) <= 1:
        return data
    
    char_index = random.randint(0, len(data) - 1)
    deleted_char = data[char_index]
    
    result = data[:char_index] + data[char_index+1:]
    print(f"    [Character Deletion] '{deleted_char}' silindi (pozisyon {char_index})")
    return result

def random_character_insertion(data):
    if not data:
        return data
    
    insert_index = random.randint(0, len(data))
    new_char = chr(random.randint(97, 122))
    
    result = data[:insert_index] + new_char + data[insert_index:]
    print(f"    [Character Insertion] '{new_char}' eklendi (pozisyon {insert_index})")
    return result

def character_swapping(data):
    if len(data) < 2:
        return data
    
    swap_index = random.randint(0, len(data) - 2)
    
    result = (data[:swap_index] + 
              data[swap_index+1] + 
              data[swap_index] + 
              data[swap_index+2:])
    
    print(f"    [Character Swapping] '{data[swap_index]}' ↔ '{data[swap_index+1]}' (pozisyon {swap_index})")
    return result

def multiple_bit_flips(data):
    if not data:
        return data
    
    num_flips = random.randint(2, min(4, len(data)))
    indices = random.sample(range(len(data)), num_flips)
    
    result = list(data)
    flipped_info = []
    
    for char_index in indices:
        char = result[char_index]
        bit_index = random.randint(0, 7)
        ascii_val = ord(char)
        corrupted_val = ascii_val ^ (1 << bit_index)
        
        if corrupted_val < 32 or corrupted_val > 126:
            corrupted_val = (corrupted_val % 95) + 32
        
        result[char_index] = chr(corrupted_val)
        flipped_info.append(f"'{char}'→'{result[char_index]}'")
    
    print(f"    [Multiple Bit Flips] {', '.join(flipped_info)}")
    return ''.join(result)

def burst_error(data):
    if len(data) < 3:
        return multiple_bit_flips(data)
    
    burst_length = random.randint(3, min(8, len(data)))
    start_index = random.randint(0, len(data) - burst_length)
    
    result = list(data)
    original_burst = data[start_index:start_index + burst_length]
    
    for i in range(start_index, start_index + burst_length):
        new_char = chr(random.randint(65, 90))
        result[i] = new_char
    
    corrupted_burst = ''.join(result[start_index:start_index + burst_length])
    print(f"    [Burst Error] '{original_burst}' → '{corrupted_burst}' (pozisyon {start_index}-{start_index + burst_length - 1})")
    return ''.join(result)

ERROR_METHODS = {
    '1': ('Bit Flip', bit_flip),
    '2': ('Character Substitution', character_substitution),
    '3': ('Character Deletion', character_deletion),
    '4': ('Random Character Insertion', random_character_insertion),
    '5': ('Character Swapping', character_swapping),
    '6': ('Multiple Bit Flips', multiple_bit_flips),
    '7': ('Burst Error', burst_error),
    '8': ('No Corruption', lambda x: x),
}

class Server:
    def __init__(self, host='localhost', port=5000, client2_port=5001):
        self.host = host
        self.port = port
        self.client2_port = client2_port
        self.error_method = '1'
        self.running = True
        
    def display_menu(self):
        print("\n" + "="*60)
        print("       SERVER - ARA DÜĞÜM + VERİ BOZUCU")
        print("="*60)
        print("\nHata Enjekte Yöntemleri:")
        for key, (name, _) in ERROR_METHODS.items():
            marker = " ← seçili" if key == self.error_method else ""
            print(f"  {key}. {name}{marker}")
        print("-"*60)
        
    def set_error_method(self, method):
        if method in ERROR_METHODS:
            self.error_method = method
            print(f"\n✓ Hata yöntemi değiştirildi: {ERROR_METHODS[method][0]}")
        else:
            print(f"\n✗ Geçersiz yöntem: {method}")
    
    def corrupt_data(self, data):
        method_name, method_func = ERROR_METHODS[self.error_method]
        print(f"  Uygulanan hata yöntemi: {method_name}")
        return method_func(data)
    
    def forward_to_client2(self, packet):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.client2_port))
                s.sendall(packet.encode('utf-8'))
                print(f"  ✓ Paket Client 2'ye iletildi")
                return True
        except ConnectionRefusedError:
            print(f"  ✗ Client 2'ye bağlanılamadı (port {self.client2_port})")
            return False
        except Exception as e:
            print(f"  ✗ Client 2'ye iletim hatası: {e}")
            return False
    
    def handle_client(self, client_socket, address):
        try:
            print(f"\n{'='*60}")
            print(f"[+] Client 1 bağlandı: {address}")
            
            packet = client_socket.recv(4096).decode('utf-8')
            print(f"  Alınan paket: {packet}")
            
            try:
                parts = packet.split('|')
                if len(parts) != 3:
                    raise ValueError("Geçersiz paket formatı")
                
                data, method, control_info = parts
                print(f"  Veri: {data}")
                print(f"  Yöntem: {method}")
                print(f"  Kontrol Bilgisi: {control_info}")
                
                print(f"\n  [Veri Bozma İşlemi]")
                corrupted_data = self.corrupt_data(data)
                print(f"  Orijinal veri: {data}")
                print(f"  Bozulmuş veri: {corrupted_data}")
                
                corrupted_packet = f"{corrupted_data}|{method}|{control_info}"
                print(f"\n  Bozulmuş paket: {corrupted_packet}")
                
                self.forward_to_client2(corrupted_packet)
                
                client_socket.sendall("Paket alındı ve işlendi.".encode('utf-8'))
                
            except ValueError as e:
                print(f"  ✗ Paket işleme hatası: {e}")
                client_socket.sendall(f"Hata: {e}".encode('utf-8'))
                
        except Exception as e:
            print(f"  ✗ İstemci işleme hatası: {e}")
        finally:
            client_socket.close()
            print(f"[-] Client 1 bağlantısı kapatıldı")
    
    def input_handler(self):
        while self.running:
            try:
                user_input = input().strip()
                if user_input.lower() == 'q':
                    print("\nServer kapatılıyor...")
                    self.running = False
                    break
                elif user_input.lower() == 'm':
                    self.display_menu()
                elif user_input in ERROR_METHODS:
                    self.set_error_method(user_input)
                else:
                    print("Geçersiz giriş. 'm' ile menü, '1-8' ile yöntem, 'q' ile çıkış")
            except EOFError:
                break
    
    def start(self):
        self.display_menu()
        print(f"\nServer başlatılıyor: {self.host}:{self.port}")
        print(f"Client 2 port: {self.client2_port}")
        print("\nKomutlar: '1-8' yöntem seç | 'm' menü | 'q' çıkış")
        print("-"*60)
        
        input_thread = threading.Thread(target=self.input_handler, daemon=True)
        input_thread.start()
        
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        server_socket.settimeout(1.0)
        
        print(f"✓ Server dinlemede: {self.host}:{self.port}")
        
        try:
            while self.running:
                try:
                    client_socket, address = server_socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address)
                    )
                    client_thread.start()
                except socket.timeout:
                    continue
        except KeyboardInterrupt:
            print("\n\nServer kapatılıyor (Ctrl+C)...")
        finally:
            server_socket.close()
            print("Server kapatıldı.")

def main():
    server = Server(host='localhost', port=5000, client2_port=5001)
    server.start()

if __name__ == "__main__":
    main()
