#!/usr/bin/python3

import ccm
import pytest
import base64

sample = 'MJEAhaGscNcK6zj0Tj13pocV1q6x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w=='
sample_bin = bytearray(base64.b64decode(sample))


@pytest.fixture
def cookie():
    '''
    Generates a sample cookie object.

    Paramaters:
        None

    Returns:
        cookie                      (CryptedCookie)         Sample cookie object
    '''
    cookie = ccm.CryptedCookie(sample)
    return cookie


@pytest.fixture
def padding_list_8():
    '''
    Generates an expected list of cookie values to detect padding oracle vulnerabilities with a blocksize
    of 8 byte.

    Paramaters:
        None

    Returns:
        padding_list                (list[string])          List of expected cookie values
    '''
    padding_list = []
    for i in range(0, 255 + 1):
        mod_sample = sample_bin.copy()
        mod_sample[len(mod_sample) - 8 - 1] = i
        decoded = base64.b64encode(mod_sample)
        decoded = decoded.decode('utf-8')
        padding_list.append(decoded)

    return padding_list


@pytest.fixture
def padding_list_16():
    '''
    Generates an expected list of cookie values to detect padding oracle vulnerabilities with a blocksize
    of 16 byte.

    Paramaters:
        None

    Returns:
        padding_list                (list[string])          List of expected cookie values
    '''
    padding_list = []
    for i in range(0, 255 + 1):
        mod_sample = sample_bin.copy()
        mod_sample[len(mod_sample) - 16 - 1] = i
        decoded = base64.b64encode(mod_sample)
        decoded = decoded.decode('utf-8')
        padding_list.append(decoded)

    return padding_list


def test_padding_8_16_generator(cookie, padding_list_8, padding_list_16):
    '''
    Test if the padding generator is correcct for both blocksizes (8, 16).

    Paramaters:
        cookie                  (fixture)               CryptedCookie object
        padding_list_8          (list[string])          Expected result for blocksize 8
        padding_list_16         (list[string])          Expected result for blocksize 16
    '''
    generator = cookie.padding_generator()

    for item in generator:

        if item in padding_list_8:
            padding_list_8.remove(item)

        elif item in padding_list_16:
            padding_list_16.remove(item)

    assert len(padding_list_8) + len(padding_list_16) == 0


def test_padding_8_generator(cookie, padding_list_8):
    '''
    Test if the padding generator is correcct for blocksizes 8.

    Paramaters:
        cookie                  (fixture)               CryptedCookie object
        padding_list_8          (list[string])          Expected result for blocksize 8
    '''
    cookie.block_sizes = [8]
    generator = cookie.padding_generator()

    for item in generator:

        if item in padding_list_8:
            padding_list_8.remove(item)

    assert len(padding_list_8) == 0


def test_padding_16_generator(cookie, padding_list_16):
    '''
    Test if the padding generator is correcct for blocksizes 16.

    Paramaters:
        cookie                  (fixture)               CryptedCookie object
        padding_list_16         (list[string])          Expected result for blocksize 16
    '''
    cookie.block_sizes = [16]
    generator = cookie.padding_generator()

    for item in generator:

        if item in padding_list_16:
            padding_list_16.remove(item)

    assert len(padding_list_16) == 0
