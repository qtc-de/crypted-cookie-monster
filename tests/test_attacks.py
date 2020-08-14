#!/usr/bin/python3

import ccm
import pytest
import binascii

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

key = b'Sixteen byte key'
IV = b'Sixteen bytes IV'

cipher_ecb = AES.new(key, AES.MODE_ECB)
cipher_cbc = AES.new(key, AES.MODE_CBC, iv=IV)

# |----- 00 -----|------ 01 -----|------ 02 -----|------ 03 -----|------ 04 -----|
# |----- iv -----|timestap=1597405984&username=username-that-fills&role=guest
sample_1 = b'timestap=1597405984&username=username-that-fills&role=guest'

# |----- 00 -----|------ 01 -----|------ 02 -----|------ 03 -----|------ 04 -----|------ 05 -----|
# |----- iv -----|timestap=1597405984&username=username-that-fills&role=guest&language=en
sample_2 = b'timestap=1597405984&username=username-that-fills&role=guest&language=en'

# |----- 00 -----|------ 01 -----|------ 02 -----|------ 03 -----|------ 04 -----|------ 05 -----|
# |----- iv -----|timestap=1597405984&username=username-that-fills&isadmin=0&language=en
sample_3 = b'timestap=1597405984&username=username-that-fills&isadmin=0&language=en'

# |------ 00 -----|------ 01 -----|------ 02 -----|------ 03 -----|------ 04 -----|
# |timestap=1597405984&username=use1&ame-that-fills&rid=44&isadmin=0&language=en
sample_4 = b'timestap=1597405984&username=use1;ame-that-fills&rid=44&isadmin=0&language=en'

sample_1_cbc = binascii.hexlify(IV + cipher_cbc.encrypt(pad(sample_1, AES.block_size))).decode('utf-8')
sample_2_cbc = binascii.hexlify(IV + cipher_cbc.encrypt(pad(sample_2, AES.block_size))).decode('utf-8')
sample_3_cbc = binascii.hexlify(IV + cipher_cbc.encrypt(pad(sample_3, AES.block_size))).decode('utf-8')
sample_4_ecb = binascii.hexlify(cipher_ecb.encrypt(pad(sample_4, AES.block_size))).decode('utf-8')

#####################################################################
#                          Aimed Flipping                           #
#####################################################################
aimed_flipping_format = "crypted, current, desired, start, end, check"
aimed_flipping_samples = [
        (sample_1_cbc, 'guest', 'admin', 0, -1, '&role=admin'),
        (sample_2_cbc, 'guest', 'admin', 0, -1, '&role=admin&'),
        (sample_3_cbc, '=0&', '=1&', 0, -1, '&isadmin=1&'),
        (sample_1_cbc, 'guest', 'admin', 3, 3, '&role=admin'),
        (sample_2_cbc, 'guest', 'admin', 0, 3, '&role=admin&'),
        (sample_3_cbc, '=0&', '=1&', 1, 3, '&isadmin=1&'),
]


@pytest.mark.parametrize(aimed_flipping_format, aimed_flipping_samples)
def test_aimed_flipping(crypted, current, desired, start, end, check):

    cookie = ccm.CryptedCookie(crypted, block_sizes=[16])
    generator = cookie.aimed_flipping_generator(current, desired, 0, -1, start, end)

    result = False
    for item in generator:

        cipher = AES.new(key, AES.MODE_CBC, iv=IV)
        item = binascii.unhexlify(item)
        item = cipher.decrypt(item)
        if check.encode('utf-8') in item:
            result = True

    assert result is True


#####################################################################
#                           Bit Flipping                            #
#####################################################################
bit_flipping_format = "crypted, start, end, check"
bit_flipping_samples = [
        (sample_3_cbc, 0, -1, '&isadmin=1&'),
        (sample_3_cbc, 3, 3, '&isadmin=1&'),
        (sample_3_cbc, 0, 3, '&isadmin=1&'),
        (sample_3_cbc, 1, 3, '&isadmin=1&'),
]


@pytest.mark.parametrize(bit_flipping_format, bit_flipping_samples)
def test_bit_flipping(crypted, start, end, check):

    cookie = ccm.CryptedCookie(crypted, block_sizes=[16])
    generator = cookie.flipping_generator(0, -1, start, end)

    result = False
    for item in generator:

        cipher = AES.new(key, AES.MODE_CBC, iv=IV)
        item = binascii.unhexlify(item)
        item = cipher.decrypt(item)
        if check.encode('utf-8') in item:
            result = True

    assert result is True


#####################################################################
#                         Block Shuffeling                          #
#####################################################################
shuffle_format = "crypted, start, end, target_blocks, check"
shuffle_samples = [
        (sample_4_ecb, 0, -1, [2], '&isadmin=1;'),
        (sample_4_ecb, 3, 3, [2], '&isadmin=1;'),
        (sample_4_ecb, 3, 5, [2], '&isadmin=1;'),
        (sample_4_ecb, 0, -1, [3], '&isadmin=1;'),
        (sample_4_ecb, 0, 2, [3], '&isadmin=1;'),
        (sample_4_ecb, 2, 2, [3], '&isadmin=1;'),
]


@pytest.mark.parametrize(shuffle_format, shuffle_samples)
def test_shuffeling(crypted, start, end, target_blocks, check):

    cookie = ccm.CryptedCookie(crypted, block_sizes=[16])
    generator = cookie.shuffeling_generator(start=start, end=end, target_blocks=target_blocks)

    result = False
    for item in generator:

        cipher = AES.new(key, AES.MODE_ECB)
        item = binascii.unhexlify(item)
        item = cipher.decrypt(item)
        if check.encode('utf-8') in item:
            result = True

    assert result is True


#####################################################################
#                          Full Shuffeling                          #
#####################################################################
full_shuffle_format = "crypted, start, end, check"
full_shuffle_samples = [
        (sample_4_ecb, 0, -1, '&isadmin=1;'),
        (sample_4_ecb, 2, 3, '&isadmin=1;'),
        (sample_4_ecb, 2, 4, '&isadmin=1;'),
]


@pytest.mark.parametrize(full_shuffle_format, full_shuffle_samples)
def test_full_shuffeling(crypted, start, end, check):

    cookie = ccm.CryptedCookie(crypted, block_sizes=[16])
    generator = cookie.full_shuffeling_generator(start=start, end=end)

    result = False
    for item in generator:

        cipher = AES.new(key, AES.MODE_ECB)
        item = binascii.unhexlify(item)
        item = cipher.decrypt(item)
        if check.encode('utf-8') in item:
            result = True

    assert result is True


#####################################################################
#                          Padding Oracle                           #
#####################################################################
padding_format = "crypted, padding"
padding_samples = [(sample_1_cbc, 0x5), (sample_2_cbc, 0x9), (sample_3_cbc, 0xa)]


@pytest.mark.parametrize(padding_format, padding_samples)
def test_padding(crypted, padding):

    cookie = ccm.CryptedCookie(crypted, block_sizes=[16])
    generator = cookie.padding_generator()

    count = 0
    for item in generator:

        cipher = AES.new(key, AES.MODE_CBC, iv=IV)
        item = binascii.unhexlify(item)
        item = cipher.decrypt(item)

        try:
            item = unpad(item, 16)
        except ValueError:
            count += 1

    # Imagine the original padding is 030303. Flipping the last byte
    # of the padding, two valid paddings can occur: 03 and 01. So, if
    # the original padding is != 0, there will be 256 - 2 = 254 padding
    # violations. If the original padding is == 0, it should be 255.
    if padding == 0x1:
        assert count == 255
    else:
        assert count == 254
