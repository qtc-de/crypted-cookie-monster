#!/usr/bin/python3

import ccm
import pytest
import base64
from urllib.parse import unquote

current = 'user;l'
desired = 'admin;'
xored = b'\x14\x17\x08\x1b\x55\x57'

sample_1 = 'MJEAhaGscNcK6zj0Tj13pocV1q6x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w=='
sample_1_bin = base64.b64decode(sample_1)

aimed_flipping_format = 'cookie_sample, counts, positions, values, block_size'
aimed_flipping_samples = [
        (sample_1, [0, 1], [0, 0], [sample_1_bin[0] ^ xored[0], sample_1_bin[0]], 8),
        (sample_1, [0, 2], [5, 5], [sample_1_bin[5] ^ xored[5], sample_1_bin[5] ^ xored[3]], 8),
        (sample_1, [3, 6], [8, 16], [sample_1_bin[8] ^ xored[0], sample_1_bin[16] ^ xored[0]], 8),
        (sample_1, [0, 1], [0, 0], [sample_1_bin[0] ^ xored[0], sample_1_bin[0]], 16),
        (sample_1, [0, 2], [5, 5], [sample_1_bin[5] ^ xored[5], sample_1_bin[5] ^ xored[3]], 16),
        (sample_1, [11, 22], [16, 32], [sample_1_bin[16] ^ xored[0], sample_1_bin[32] ^ xored[0]], 16),
        ]

aimed_offset_flipping_format = 'cookie_sample, counts, positions, values, block_size, start, end, skipped'
aimed_offset_flipping_samples = [
        (sample_1, [0, 1], [16, 16], [sample_1_bin[16] ^ xored[0], sample_1_bin[16]], 8, 16, 31, 0),
        (sample_1, [4, 5], [31, 31], [sample_1_bin[31], sample_1_bin[31] ^ xored[5]], 8, 16, 31, 0),
        (sample_1, [6, 7], ['skipped', 'skipped'], ['skipped', 'skipped'], 8, 16, 31, 2),

        (sample_1, [0, 1], [16, 16], [sample_1_bin[16] ^ xored[0], sample_1_bin[16]], 16, 16, 31, 0),
        (sample_1, [4, 5], [19, 21], [sample_1_bin[19], sample_1_bin[21] ^ xored[0]], 16, 16, 31, 0),
        (sample_1, [9, 10], [31, 31], [sample_1_bin[31], sample_1_bin[31] ^ xored[5]], 16, 16, 31, 0),
        (sample_1, [11, 12], ['skipped', 'skipped'], ['skipped', 'skipped'], 16, 16, 31, 2),
        ]

aimed_block_offset_flipping_format = 'cookie_sample, counts, positions, values, block_size, start, end, skipped'
aimed_block_offset_flipping_samples = [
        (sample_1, [0, 1], [0, 6], [sample_1_bin[0] ^ xored[0], sample_1_bin[6] ^ xored[5]], 8, 0, 0, 0),
        (sample_1, [0, 1], [16, 16], [sample_1_bin[16] ^ xored[0], sample_1_bin[16]], 8, 2, 2, 0),
        (sample_1, [4, 5], [31, 31], [sample_1_bin[31], sample_1_bin[31] ^ xored[5]], 8, 2, 3, 0),
        (sample_1, [6, 7], ['skipped', 'skipped'], ['skipped', 'skipped'], 8, 2, 3, 2),

        (sample_1, [0, 1], [16, 16], [sample_1_bin[16] ^ xored[0], sample_1_bin[16]], 16, 1, 1, 0),
        (sample_1, [4, 5], [19, 21], [sample_1_bin[19], sample_1_bin[21] ^ xored[0]], 16, 1, 1, 0),
        (sample_1, [9, 10], [31, 31], [sample_1_bin[31], sample_1_bin[31] ^ xored[5]], 16, 1, 1, 0),
        (sample_1, [11, 12], [32, 32], [sample_1_bin[32] ^ xored[0], sample_1_bin[32]], 16, 1, 2, 0),
        (sample_1, [20, 21], [47, 47], [sample_1_bin[47], sample_1_bin[47] ^ xored[5]], 16, 1, 2, 0),
        (sample_1, [11, 12], ['skipped', 'skipped'], ['skipped', 'skipped'], 16, 1, 1, 2),
        ]


@pytest.mark.parametrize(aimed_flipping_format, aimed_flipping_samples)
def test_aimed_flipping(cookie_sample, counts, positions, values, block_size):
    '''
    Test whether aimed flips lead to the expected result.

    Parameters:
        cookie_sample           (string)            Cookie sample value in b64
        counts                  (list[int])         Generator iterations to apply check on
        positions               (list[int])         Byterray positions where the check applies
        values                  (list[int])         Expected values on the check positions
        block_size              (int)               Block size to use

    Returns:
        None
    '''
    cookie = ccm.CryptedCookie(cookie_sample, block_sizes=[block_size])
    generator = cookie.aimed_flipping_generator(current, desired, 0, -1, None, None)

    counter = 0
    for item in generator:

        if counter in counts:

            position = positions.pop(0)
            value = values.pop(0)

            decoded = unquote(item)
            decoded = base64.b64decode(decoded)
            assert decoded[position] == value

        counter += 1


@pytest.mark.parametrize(aimed_offset_flipping_format, aimed_offset_flipping_samples)
def test_aimed_offset_flipping(cookie_sample, counts, positions, values, block_size, start, end, skipped):
    '''
    Test whether aimed flips lead to the expected results when used with byte offsets.

    Parameters:
        cookie_sample           (string)            Cookie sample value in b64
        counts                  (list[int])         Generator iterations to apply check on
        positions               (list[int])         Byterray positions where the check applies
        values                  (list[int])         Expected values on the check positions
        block_size              (int)               Block size to use
        start                   (int)               Byte position to start on
        end                     (int)               Byte position to end on
        skipped                 (int)               Expected number of skipped positions

    Returns:
        None
    '''
    cookie = ccm.CryptedCookie(cookie_sample, block_sizes=[block_size])
    generator = cookie.aimed_flipping_generator(current, desired, start, end, None, None)

    counter = 0
    for item in generator:

        if counter in counts:

            position = positions.pop(0)
            value = values.pop(0)

            decoded = unquote(item)
            decoded = base64.b64decode(decoded)
            assert decoded[position] == value

        counter += 1

    assert len(positions) == skipped


@pytest.mark.parametrize(aimed_block_offset_flipping_format, aimed_block_offset_flipping_samples)
def test_aimed_block_offset_flipping(cookie_sample, counts, positions, values, block_size, start, end, skipped):
    '''
    Test whether aimed flips lead to the expected results when used with block offsets.

    Parameters:
        cookie_sample           (string)            Cookie sample value in b64
        counts                  (list[int])         Generator iterations to apply check on
        positions               (list[int])         Byterray positions where the check applies
        values                  (list[int])         Expected values on the check positions
        block_size              (int)               Block size to use
        start                   (int)               Block position to start on
        end                     (int)               Block position to end on
        skipped                 (int)               Expected number of skipped positions

    Returns:
        None
    '''
    cookie = ccm.CryptedCookie(cookie_sample, block_sizes=[block_size])
    generator = cookie.aimed_flipping_generator(current, desired, 0, -1, start, end)

    counter = 0
    for item in generator:

        if counter in counts:

            position = positions.pop(0)
            value = values.pop(0)

            decoded = unquote(item)
            decoded = base64.b64decode(decoded)
            assert decoded[position] == value

        counter += 1

    assert len(positions) == skipped
