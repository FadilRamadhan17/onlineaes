class PureAES:
    def __init__(self, key):
        # Standardize key to exactly 16 bytes
        if isinstance(key, str):
            key = key.encode('utf-8')
        self.key = key.ljust(16, b'\0')[:16]
        
        # Initialize S-box dan inverse S-box
        self.sbox = self._generate_sbox()
        self.inv_sbox = self._generate_inv_sbox()
        
        # Konstanta untuk key expansion
        self.rcon = [
            0x01, 0x02, 0x04, 0x08, 0x10, 
            0x20, 0x40, 0x80, 0x1B, 0x36
        ]
        
        # Expanded key
        self.round_keys = self._key_expansion()

    def _generate_sbox(self):
        # Implementasi S-box dari matematika kriptografi
        sbox = [[0 for _ in range(16)] for _ in range(16)]
        for i in range(256):
            # Transformasi invers dalam medan Galois
            if i == 0:
                sbox[i >> 4][i & 0x0F] = 0x63
            else:
                inv = self._modular_multiplicative_inverse(i)
                # Transformasi bit
                transformed = inv
                transformed ^= (transformed << 1) & 0xFF
                transformed ^= (transformed << 2) & 0xFF
                transformed ^= (transformed << 4) & 0xFF
                transformed ^= 0x63
                sbox[i >> 4][i & 0x0F] = transformed & 0xFF
        return sbox

    def _generate_inv_sbox(self):
        # Inverse S-box
        inv_sbox = [[0 for _ in range(16)] for _ in range(16)]
        for i in range(256):
            # Balik proses S-box
            value = self.sbox[i >> 4][i & 0x0F]
            inv_sbox[value >> 4][value & 0x0F] = i
        return inv_sbox

    def _modular_multiplicative_inverse(self, x):
        # Algoritma Extended Euclidean untuk invers multiplikatif
        def egcd(a, b):
            if a == 0:
                return b, 0, 1
            else:
                gcd, y, x = egcd(b % a, a)
                return gcd, x - (b // a) * y, y

        _, x, _ = egcd(x, 0x11B)
        return x % 256

    def _key_expansion(self):
        # Ekspansi kunci AES
        key_words = [int.from_bytes(self.key[i:i+4], 'big') for i in range(0, 16, 4)]
        expanded_keys = key_words.copy()

        for i in range(4, 44):
            temp = expanded_keys[i-1]
            if i % 4 == 0:
                # Rotasi, substitusi, XOR dengan Rcon
                temp = self._sub_word(self._rot_word(temp)) ^ (self.rcon[(i//4)-1] << 24)
            expanded_keys.append(temp ^ expanded_keys[i-4])

        return expanded_keys

    def _rot_word(self, word):
        # Rotasi byte paling signifikan ke posisi paling rendah
        return ((word << 8) & 0xFFFFFFFF) | (word >> 24)

    def _sub_word(self, word):
        # Substitusi byte menggunakan S-box
        return (self._sbox_transform((word >> 24) & 0xFF) << 24 |
                self._sbox_transform((word >> 16) & 0xFF) << 16 |
                self._sbox_transform((word >> 8) & 0xFF) << 8 |
                self._sbox_transform(word & 0xFF))

    def _sbox_transform(self, byte):
        # Transformasi byte melalui S-box
        return self.sbox[byte >> 4][byte & 0x0F]

    def _add_round_key(self, state, round_key):
        # XOR state dengan round key
        for i in range(4):
            for j in range(4):
                state[i][j] ^= (round_key[i] >> (24 - j * 8)) & 0xFF
        return state

    def _sub_bytes(self, state):
        # Substitusi bytes menggunakan S-box
        for i in range(4):
            for j in range(4):
                state[i][j] = self.sbox[state[i][j] >> 4][state[i][j] & 0x0F]
        return state

    def _shift_rows(self, state):
        # Shift baris state
        state[1] = state[1][1:] + state[1][:1]
        state[2] = state[2][2:] + state[2][:2]
        state[3] = state[3][3:] + state[3][:3]
        return state

    def _mix_columns(self, state):
        # Mix kolom dalam state
        def gmul(a, b):
            # Perkalian Galois
            p = 0
            for _ in range(8):
                if b & 1:
                    p ^= a
                hi_bit_set = a & 0x80
                a = (a << 1) & 0xFF
                if hi_bit_set:
                    a ^= 0x1B
                b >>= 1
            return p

        new_state = [[0 for _ in range(4)] for _ in range(4)]
        for c in range(4):
            new_state[0][c] = (gmul(state[0][c], 2) ^ 
                               gmul(state[1][c], 3) ^ 
                               state[2][c] ^ 
                               state[3][c]) & 0xFF
            new_state[1][c] = (state[0][c] ^ 
                               gmul(state[1][c], 2) ^ 
                               gmul(state[2][c], 3) ^ 
                               state[3][c]) & 0xFF
            new_state[2][c] = (state[0][c] ^ 
                               state[1][c] ^ 
                               gmul(state[2][c], 2) ^ 
                               gmul(state[3][c], 3)) & 0xFF
            new_state[3][c] = (gmul(state[0][c], 3) ^ 
                               state[1][c] ^ 
                               state[2][c] ^ 
                               gmul(state[3][c], 2)) & 0xFF
        return new_state
    
    def _inv_shift_rows(self, state):
        # Invers shift baris (geser ke kanan)
        state[1] = state[1][-1:] + state[1][:-1]
        state[2] = state[2][-2:] + state[2][:-2]
        state[3] = state[3][-3:] + state[3][:-3]
        return state

    def _inv_sub_bytes(self, state):
        # Invers substitusi bytes menggunakan inverse S-box
        for i in range(4):
            for j in range(4):
                state[i][j] = self.inv_sbox[state[i][j] >> 4][state[i][j] & 0x0F]
        return state

    def _inv_mix_columns(self, state):
        # Invers mix kolom
        def gmul(a, b):
            # Perkalian Galois
            p = 0
            for _ in range(8):
                if b & 1:
                    p ^= a
                hi_bit_set = a & 0x80
                a = (a << 1) & 0xFF
                if hi_bit_set:
                    a ^= 0x1B
                b >>= 1
            return p

        new_state = [[0 for _ in range(4)] for _ in range(4)]
        for c in range(4):
            new_state[0][c] = (gmul(state[0][c], 0x0E) ^ 
                               gmul(state[1][c], 0x0B) ^ 
                               gmul(state[2][c], 0x0D) ^ 
                               gmul(state[3][c], 0x09)) & 0xFF
            new_state[1][c] = (gmul(state[0][c], 0x09) ^ 
                               gmul(state[1][c], 0x0E) ^ 
                               gmul(state[2][c], 0x0B) ^ 
                               gmul(state[3][c], 0x0D)) & 0xFF
            new_state[2][c] = (gmul(state[0][c], 0x0D) ^ 
                               gmul(state[1][c], 0x09) ^ 
                               gmul(state[2][c], 0x0E) ^ 
                               gmul(state[3][c], 0x0B)) & 0xFF
            new_state[3][c] = (gmul(state[0][c], 0x0B) ^ 
                               gmul(state[1][c], 0x0D) ^ 
                               gmul(state[2][c], 0x09) ^ 
                               gmul(state[3][c], 0x0E)) & 0xFF
        return new_state

    def encrypt(self, plaintext):
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        
        padding_length = 16 - (len(plaintext) % 16)
        padded_text = plaintext + bytes([padding_length] * padding_length)
        
        encrypted_blocks = []
        for i in range(0, len(padded_text), 16):
            block = padded_text[i:i+16]
            encrypted_block = self._encrypt_block(block)
            encrypted_blocks.append(encrypted_block)
        
        return bytes(sum(encrypted_blocks, [])).hex()

    def _encrypt_block(self, block):
        # Konversi blok ke state 4x4
        state = [list(block[i:i+4]) for i in range(0, 16, 4)]
        
        # Initial round key addition
        state = self._add_round_key(state, self.round_keys[:4])
        
        # 9 round utama
        for round in range(1, 10):
            state = self._sub_bytes(state)
            state = self._shift_rows(state)
            state = self._mix_columns(state)
            state = self._add_round_key(state, self.round_keys[4*round:4*(round+1)])
        
        # Round terakhir (tanpa mix columns)
        state = self._sub_bytes(state)
        state = self._shift_rows(state)
        state = self._add_round_key(state, self.round_keys[40:])
        
        # Konversi state kembali ke bytes
        return sum(state, [])

    def decrypt(self, ciphertext):
    # Konversi ciphertext hex ke bytes
        if isinstance(ciphertext, str):
            ciphertext = bytes.fromhex(ciphertext)
        
        # Dekripsi blok
        decrypted_blocks = []
        for i in range(0, len(ciphertext), 16):
            block = ciphertext[i:i+16]
            decrypted_block = self._decrypt_block(block)
            decrypted_blocks.append(decrypted_block)
        
        # Gabungkan blok dan hapus padding
        decrypted_data = bytes(sum(decrypted_blocks, []))
        
        # Hapus padding PKCS7
        padding_length = decrypted_data[-1]
        # Validasi padding sebelum menghapusnya
        if padding_length > 0 and padding_length <= 16:
            # Cek apakah padding valid (semua byte padding harus sama dengan padding_length)
            if all(b == padding_length for b in decrypted_data[-padding_length:]):
                return decrypted_data[:-padding_length].decode('utf-8')
        
        # Jika padding tidak valid, kembalikan data tanpa menghapus padding
        return decrypted_data.decode('utf-8')

    def _decrypt_block(self, block):
    # Konversi blok ke state 4x4
        state = [list(block[i:i+4]) for i in range(0, 16, 4)]
        
        # Initial round key addition
        state = self._add_round_key(state, self.round_keys[40:])
        
        # 9 main rounds
        for round in range(9, 0, -1):
            state = self._inv_shift_rows(state)
            state = self._inv_sub_bytes(state)
            state = self._add_round_key(state, self.round_keys[4*round:4*(round+1)])
            state = self._inv_mix_columns(state)
        
        # Final round (no InvMixColumns)
        state = self._inv_shift_rows(state)
        state = self._inv_sub_bytes(state)
        state = self._add_round_key(state, self.round_keys[:4])
        
        # Konversi state kembali ke bytes
        return sum(state, [])