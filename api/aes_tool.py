#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AES-GCM 加密与解密命令行工具
作者: ChatGPT (为 Cheng Fang 编写)
"""

import base64
import os
import getpass
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def encrypt_message():
    password = getpass.getpass("请输入加密口令: ").encode()
    plaintext = input("请输入要加密的文本: ").encode()

    # 生成 32 字节密钥（从口令简单派生）
    from hashlib import sha256
    key = sha256(password).digest()

    # 随机 12 字节 nonce
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)

    # 输出 base64 编码的结果（nonce + ciphertext）
    result = base64.b64encode(nonce + ciphertext).decode()
    print("\n加密结果（复制保存）:")
    print(result)


def decrypt_message():
    password = getpass.getpass("请输入解密口令: ").encode()
    data_b64 = input("请输入要解密的Base64字符串: ").strip()

    from hashlib import sha256
    key = sha256(password).digest()

    try:
        data = base64.b64decode(data_b64)
        nonce, ciphertext = data[:12], data[12:]
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        print("\n解密结果:")
        print(plaintext.decode())
    except Exception as e:
        print("❌ 解密失败，可能是口令错误或数据损坏。")
        print("错误信息:", e)


def main():
    import sys
    if len(sys.argv) != 2 or sys.argv[1] not in ["encrypt", "decrypt"]:
        print("用法:")
        print("  python aes_tool.py encrypt   # 加密模式")
        print("  python aes_tool.py decrypt   # 解密模式")
        return

    if sys.argv[1] == "encrypt":
        encrypt_message()
    else:
        decrypt_message()


if __name__ == "__main__":
    main()
