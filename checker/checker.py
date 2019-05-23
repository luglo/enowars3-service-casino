import requests
import json
import random
import string
import time
import os
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from enochecker import BaseChecker, BrokenServiceException, run
from enochecker.utils import *

session = requests.Session()

def bytes_arr_to_int_arr(bytes_arr):
    result = []
    for b in bytes_arr:
        result.append(int.from_bytes([b], byteorder='big', signed=False))
    return result

def decrypt_aes(key, iv, enc_msg):
    #aesSuite = AES.new(key, AES.MODE_CTR, nonce=iv[:8], initial_value=iv[8:])
    #return aesSuite.decrypt(enc_msg)


    with open(".aes_msg_enc","w") as f:
        f.write(json.dumps([bytes_arr_to_int_arr(key), bytes_arr_to_int_arr(iv), bytes_arr_to_int_arr(enc_msg)]))

    #TODO: subprocess and stdout
    exit_code = os.system("julia aes_decryptor.jl")

    print(exit_code)
    if exit_code != 0:
        raise BrokenServiceException

    with open(".aes_msg", "r") as f:
        msg = json.loads(f.read())

    return bytes(msg).decode('utf-8').rstrip('\x00')


#TODO: change for use in the checker
def decode_crypto_msg(enc_msg_json):

    data = json.loads(enc_msg_json)

    #convert int list to bytes
    enc_msg_aes = bytes(data[0])
    iv = bytes(data[1])
    enc_aes_key = bytes(data[2])

    print("Encrypted AES msg:", enc_msg_aes)
    print("IV:", iv)
    print("Encrypted AES key:", enc_aes_key)

    #TODO: validate input
    aes_key = rsa_decode(enc_aes_key)

    decoded_msg = decrypt_aes(aes_key, iv, enc_msg_aes)

    return decoded_msg

def rsa_decode(enc_aes_key):
    with open("assets/private.pem") as aeskey_file:
        key = RSA.import_key(aeskey_file.read(), passphrase="enowars")

    cipher_rsa = PKCS1_OAEP.new(key)
    #TODO: try - invalid input?
    enc_key_bytes = cipher_rsa.decrypt(enc_aes_key)

    return enc_key_bytes


def rsa_sign_message(msg):
    with open("assets/private.pem") as aeskey_file:
        key = RSA.import_key(aeskey_file.read(), passphrase="enowars")

    msg_bytes = bytearray()
    msg_bytes.extend(map(ord, msg))
    hash = SHA256.new(msg_bytes)
    signature = pkcs1_15.new(key).sign(hash)

    hash_list = []
    #convert back to int list

    for b in signature:

        hash_list.append(int.from_bytes([b], byteorder='big', signed=False))
    #print(enc_key_list)
    return json.dumps([msg,hash_list])



def generate_random_string(length = 3):
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.choice(alphabet) for i in range(length))



class CasinoChecker(BaseChecker):
    debug_print = True

    def readline_expect_multiline(self, telnet_session, msg, pls_print=False):
        for m in msg.split('\n'):
            if print:
                tmp = readline_expect(telnet_session, m)
                print(tmp)
                self.debug(tmp)
            else:
                readline_expect(telnet_session, m)


    def intro(self, t):
        self.readline_expect_multiline(t, "Entering...", self.debug_print)
        self.readline_expect_multiline(t, self.dictionary["spacer"], self.debug_print)
        self.readline_expect_multiline(t, self.dictionary["welcome"], self.debug_print)
        self.readline_expect_multiline(t, self.dictionary["spacer"], self.debug_print)
        self.readline_expect_multiline(t, "Your balance is: 0", self.debug_print)
        self.readline_expect_multiline(t, self.dictionary["reception_0"], self.debug_print)


    def goto_cryptomat(self, t):
        t.write("b\n")
        self.readline_expect_multiline(t, self.dictionary["reception_2"], self.debug_print)
        self.readline_expect_multiline(t, self.dictionary["spacer"], self.debug_print)
        self.readline_expect_multiline(t, self.dictionary["bathroom_0"], self.debug_print)
        t.write("w\n")
        self.readline_expect_multiline(t, self.dictionary["bathroom_1"], self.debug_print)
        self.readline_expect_multiline(t, self.dictionary["bathroom_4"], self.debug_print)
        t.write("v\n")
        self.readline_expect_multiline(t, self.dictionary["spacer"], self.debug_print)
        self.readline_expect_multiline(t, self.dictionary["cryptomat_0"], self.debug_print)

    def goto_games(self, t):
        t.write("g\n")
        self.readline_expect_multiline(t, self.dictionary["spacer"], self.debug_print)
        self.readline_expect_multiline(t, self.dictionary["gamble_0"], self.debug_print)
        self.readline_expect_multiline(t, "black_jack\nslot_machine\nroulette", self.debug_print)
        self.readline_expect_multiline(t, self.dictionary["gamble_1"], self.debug_print)

    def insert_table_flag(self, t):
        identifier = generate_random_string(20)
        minimum = "1000000000000000000"
        passphrase = generate_random_string(20)

        t.write("c\n")
        self.readline_expect_multiline(t, self.dictionary["table_12"], self.debug_print)
        t.write(identifier + "\n")
        self.readline_expect_multiline(t, self.dictionary["table_6"], self.debug_print)
        t.write(self.flag + "\n")
        self.readline_expect_multiline(t, self.dictionary["table_8"], self.debug_print)
        t.write(minimum + "\n")
        self.readline_expect_multiline(t, self.dictionary["table_10"], self.debug_print)
        t.write(passphrase + "\n")
        self.readline_expect_multiline(t, self.dictionary["table_15"], self.debug_print)

        self.team_db[self.flag] = (identifier, minimum, passphrase)

    with open('assets/strings.json', 'r') as f:
        dictionary = json.load(f)

    port = 6969  # default port to send requests to.

    def putflag(self):
        try:
            t = self.connect()
            self.debug("connected to {}".format(self.address))
            self.intro(t)

            if self.flag_idx == 0:
                #table-flag

                #change to games
                self.goto_games(t)

                #change to black_jack
                t.write("black_jack\n")
                self.readline_expect_multiline(t, self.dictionary["spacer"], self.debug_print)
                self.readline_expect_multiline(t, self.dictionary["table_0"], self.debug_print)

                #create a new table
                self.insert_table_flag(t)

            elif self.flag_idx == 1:
                #cryptomat-flag
                self.goto_cryptomat(t)
                t.write("o\n")
                self.readline_expect_multiline(t, self.dictionary["cryptomat_os_update_1"], self.debug_print)
                try:
                    t.write(rsa_sign_message(self.flag)+"\n")
                except:
                    raise BrokenServiceException
                self.readline_expect_multiline(t, self.dictionary["cryptomat_os_update_accept_format"], self.debug_print)
                self.readline_expect_multiline(t, self.dictionary["cryptomat_os_update_accept_signature"], self.debug_print)
                self.readline_expect_multiline(t, "Updating...", self.debug_print)
                self.readline_expect_multiline(t, "Updated", self.debug_print)

            #TODO: better leaving
            print(self.flag_round)
            t.close()
        except:
            raise BrokenServiceException("putflag didnt work")

    def getflag(self):
        try:
            t = self.connect()
            self.debug("connected to {}".format(self.address))
            self.intro(t)

            if self. flag_idx == 0:
                #change to games
                self.goto_games(t)

                #change to black_jack
                t.write("black_jack\n")
                self.readline_expect_multiline(t, self.dictionary["spacer"], self.debug_print)
                self.readline_expect_multiline(t, self.dictionary["table_0"], self.debug_print)

                #join a table
                t.write("j\n")
                #self.readline_expect_multiline(t, self.dictionary[])
                identifier, minimum, passphrase = self.team_db[self.flag]

                t.read_until(self.dictionary["table_2"] + "\n")
                t.write(identifier + "\n")
                self.readline_expect_multiline(t, self.dictionary["table_4"], self.debug_print)
                t.write(passphrase + "\n")
                self.readline_expect_multiline(t, "You approach the black_jack table " + self.flag + ". The dealer smiles at you and slightly nods his head as a greeting.", self.debug_print)
                self.readline_expect_multiline(t, self.dictionary["spacer"], self.debug_print)
                self.readline_expect_multiline(t, "How much are you willing to bet?", self.debug_print)
                self.readline_expect_multiline(t, "Your balance is: 0", self.debug_print)
                t.write("0\n")

                self.readline_expect_multiline(t, "Sorry but this is not a childs game. You can leave now.", self.debug_print)
                self.readline_expect_multiline(t, self.dictionary["gamble_4"], self.debug_print)
                self.readline_expect_multiline(t, self.dictionary["spacer"], self.debug_print)
                self.readline_expect_multiline(t, "Your balance is: 0", self.debug_print)
                self.readline_expect_multiline(t, self.dictionary["reception_0"], self.debug_print)

                t.write("l\n")


            elif self.flag_idx == 1:
                self.goto_cryptomat(t)
                #get note
                t.write("◈\n".encode("utf-8"))
                #retrieve correct dimension
                print(readline_expect(t, self.dictionary["cryptomat_3"]))
                r = t.read_until("\n")[:-1]
                try:
                    notes = json.loads(r.decode('utf-8'))
                    #TODO: adjust to round
                    difference = self.round - self.flag_round
                    dimension = notes[difference]
                except:
                    raise BrokenServiceException
                #set dimension
                t.write("🕐\n".encode("utf-8"))
                t.write(str(dimension)+"\n")

                t.write("3\n")

                print(readline_expect(t, self.dictionary["cryptomat_sender_1"]))

                for i in range(0,3):
                    print(readline_expect(t, "AES CTR:\n"))
                    print(readline_expect(t, "Message:\n"))
                    msg = t.read_until("\n")[:-1].decode('utf-8')

                    try:
                        decrypted_msg = decode_crypto_msg(msg)
                    except:
                        raise BrokenServiceException
                        print("Decrypted message: ", decrypted_msg)
                    if i == 0:
                        assert_equals(decrypted_msg , "ATOM-BOMB-CODE-START", autobyteify=True)
                    elif i == 1:
                        assert_equals(decrypted_msg , self.flag, autobyteify=True)
                    elif i == 2:

                        assert_equals(decrypted_msg , "ATOM-BOMB-CODE-END", autobyteify=True)

            #todo: better leaving
            t.close()
        except:
            raise BrokenServiceException("getflag did not work!")

    def putnoise(self):
        pass

    def getnoise(self):
        pass

    def havoc(self):
        pass


app = CasinoChecker.service
if __name__ == "__main__":
    run(CasinoChecker)
