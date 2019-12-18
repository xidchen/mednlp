#!/usr/bin/env python
# -*- coding: utf8 -*-
# author: Guowp <guowp@guahao.com>

import base64
from Crypto.Cipher import AES


class AESCipher():

    def __init__(self, iv, key):
        self.bs = 16
        self.iv = iv
        self.key = key

    def encrypt(self, raw):
        raw = self._pad(raw)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return base64.b64encode(cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return self._unpad(cipher.decrypt(enc)).decode('utf-8')

    def _pad(self, s):
        return s + (
            self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]

if __name__ == '__main__':
    data = '120109194705256531'
    key = 'ufirl39df#($)f3l'  # 16,24,32位长的密码
    aes = AESCipher('greenlineguahaow', key)
    encrypt_data = aes.encrypt(data)
    print ('encrypt_data:', encrypt_data)
    decrypt_data = aes.decrypt(encrypt_data)
    print ('decrypt_data:', decrypt_data)
