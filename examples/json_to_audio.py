from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
import base64
import json
import gzip
import argparse


def get_sf(config):
    with gzip.open(config.document_gz, 'rt') as fp:
        document = json.load(fp)
        encrypted_bytes = base64.b64decode(document["encrypted_audio"])
        key = RSA.importKey(open(config.ssh_file).read(),
                            passphrase=config.ssh_password)
        cipher = PKCS1_OAEP.new(key)

        decrypted_header = cipher.decrypt(
            encrypted_bytes[:key.size_in_bytes()])

        aes_key = decrypted_header[:AES.block_size]
        iv = decrypted_header[AES.block_size:]

        aes_cipher = AES.new(aes_key, AES.MODE_CBC,
                             iv)
        decrypted_audio = aes_cipher.decrypt(
            encrypted_bytes[key.size_in_bytes():])
        if "Ogg" == decrypted_audio[:3].decode():
            print("Ogg decrypted")
        else:
            raise Exception("Audio not starting with Ogg")
        with open(config.ogg_file, "wb") as out_fp:
            out_fp.write(decrypted_audio)


def main():
    parser = argparse.ArgumentParser(
        description='This program read audio from compresse json produced'
                    ' by zerotrigger.py',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--document_gz",
                        help="Path of the compressed json file",
                        required=True, type=str)
    parser.add_argument("--ssh_file",
                        help="private key file for audio decryption",
                        required=True)
    parser.add_argument("--ssh_password",
                        help="password of private key", default=None, type=str)
    parser.add_argument("--ogg_file",
                        help="Path of the output ogg file",
                        default="audio.ogg", type=str)
    args = parser.parse_args()
    get_sf(args)


if __name__ == "__main__":
    main()
