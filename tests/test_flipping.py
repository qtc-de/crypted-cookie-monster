#!/usr/bin/python3

import ccm
import pytest
import base64
import binascii
from urllib.parse import unquote

# The tests specified in this file ensure that bit flipping occurs in he correct positions.
# Furthermore, it is also used to test different cookie formats (b64, hex, b64 with url encoding).
# To avoid too much overhead due to the generator creation, ont flipping generator can be used
# for mulitple tests. (Almost) each test has to be used with a 'counts' parameter, which specifies
# the list of generator items to operator on.

sample_1 = 'MJEAhaGscNcK6zj0Tj13pocV1q6x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w=='
sample_2 = 'MJEAhaG%2bcNcK6zj0Tj13pocV1q6x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w=='
sample_3 = '30910085a1ac70d70aeb38f44e3d77a68715d6aeb1ec869553401d909f219c765711f5c7a434d4f0f9fc0481fb'
sample_3 += '8950594736fc344b00d41032bf148d8e3349d7'

plain_flipping_format = 'cookie_sample, counts, positions, values, format'
plain_flipping_samples = [
        (sample_1, [0x33, 0xff, 0xfea, 0x1fff], [0, 0, 0x0f, 0x1f], [0x33, 0xff, 0xea, 0xff], 'b64'),
        (sample_2, [0x33, 0xff, 0xfea, 0x1fff], [0, 0, 0x0f, 0x1f], [0x33, 0xff, 0xea, 0xff], 'b64'),
        (sample_3, [0x33, 0xff, 0xfea, 0x1fff], [0, 0, 0x0f, 0x1f], [0x33, 0xff, 0xea, 0xff], 'hex'),
        ]

offset_flipping_format = 'cookie_sample, counts, positions, values, start, stop, min, max, skipped'
offset_flipping_samples = [
        # range 20 -> 30 - bytes 5 -> 9
        #   iteration 0, position 20 -> 5
        #   iteration 4, position 20 -> 9
        #   iteration 5, position 20 -> 0xb1 (default value)
        #   iteration 6, position 21 -> 6
        #   iteration 45, position 29 (45 / 5 + 20) -> 5
        (sample_1, [0, 4, 5, 6, 45], [20, 20, 20, 21, 29], [5, 9, 0xb1, 6, 5], 20, 30, 5, 9, 0),
        # range 20 -> 30 - bytes 5 -> 9
        #   iteration 50, position 30 (50 / 5 + 20) -> 5
        #   iteration 55, position 30 (50 / 5 + 20) -> 9
        #   iteration 56, position 31 (out of bound) -> not reached in the test
        (sample_1, [50, 54, 56], [30, 30, 31], [5, 9, 'stopped'], 20, 30, 5, 9, 1),
        # range 20 -> 30 - bytes 5 -> 9
        #   iteration 0, position 20 -> 5
        #   iteration 4, position 20 -> 9
        #   iteration 5, position 20 -> 0xb1 (default value)
        #   iteration 6, position 21 -> 6
        #   iteration 45, position 29 (45 / 5 + 20) -> 5
        (sample_2, [0, 4, 5, 6, 45], [20, 20, 20, 21, 29], [5, 9, 0xb1, 6, 5], 20, 30, 5, 9, 0),
        ]

block_offset_flipping_format = 'cookie_sample, counts, positions, values, start, stop, min, max, skipped'
block_offset_flipping_samples = [
        # range 3 (start: 24 byte) -> 5 (end: 48 byte) - bytes 0 -> 8
        #   iteration 0, position 24 -> 0
        #   iteration 7, position 24 -> 7
        #   iteration 9, position 24 -> 0x53 (default value)
        #   iteration 10, position 25 -> 1
        #   iteration 48, position 29 (48 // 9 + 24) -> 3
        (sample_1, [0, 7, 9, 10, 48], [24, 24, 24, 25, 29], [0, 7, 0x53, 1, 3], 3, 5, 0, 8, 0),
        # range 3 (start: 24 byte) -> 5 (end: 48 byte) - bytes 0 -> 8
        #   iteration 144, position 40 (144 // 9 + 24) -> 0
        #   iteration 215, position 47 (215 // 9 + 24) -> 7
        #   iteration 216, position 48 (out of bound) -> not reached by the test
        (sample_1, [144, 215, 216], [40, 47, 48], [0, 8, 'stopped'], 3, 5, 0, 8, 1),
        ]


@pytest.mark.parametrize(plain_flipping_format, plain_flipping_samples)
def test_plain_flipping(cookie_sample, counts, positions, values, format):
    '''
    Tests if the bit flips are done in the correct positions. To speed up this process,
    the test allows multiple positions to be tested simoultaneously.

    Parameters:
        cookie_sample           (string)            Sample cookie in base64 or hex
        counts                  (list[int])         Generator items to check
        positions               (list[int])         Positions in the bytearray to check
        values                  (list[int])         Expected values on the specified positions
        format                  (string)            Cookie format (b64 or hex)

    Returns:
        None
    '''
    cookie = ccm.CryptedCookie(cookie_sample)
    generator = cookie.flipping_generator(0, -1, None, None, 0, 255)

    counter = 0
    for item in generator:

        if counter in counts:

            position = positions.pop(0)
            value = values.pop(0)

            if format == 'b64':
                decoded = unquote(item)
                decoded = base64.b64decode(decoded)

            else:
                decoded = binascii.unhexlify(item)

            assert decoded[position] == value

        counter += 1


@pytest.mark.parametrize(offset_flipping_format, offset_flipping_samples)
def test_offset_flipping(cookie_sample, counts, positions, values, start, stop, min, max, skipped):
    '''
    Tests if the bit flips are done in the correct position when bitflipping is used with
    a byte offset.

    Parameters:
        cookie_sample           (string)            Sample cookie in base64
        counts                  (list[int])         Generator items to check
        positions               (list[int])         Positions in the bytearray to check
        values                  (list[int])         Expected values on the specified positions
        start                   (int)               Starting point (byte) inside the bytearray
        end                     (int)               End point (byte) inside the bytearray
        min                     (int)               Minimum byte used during flipping
        max                     (int)               Maximum byte used during flipping
        skipped                 (int)               Number of positions that should not be reached

    Returns:
        None
    '''
    cookie = ccm.CryptedCookie(cookie_sample)
    generator = cookie.flipping_generator(start, stop, None, None, min, max)

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


@pytest.mark.parametrize(block_offset_flipping_format, block_offset_flipping_samples)
def test_block_offset_flipping(cookie_sample, counts, positions, values, start, stop, min, max, skipped):
    '''
    Tests if the bit flips are done in the correct position when bitflipping is used with
    a block offset.

    Parameters:
        cookie_sample           (string)            Sample cookie in base64
        counts                  (list[int])         Generator items to check
        positions               (list[int])         Positions in the bytearray to check
        values                  (list[int])         Expected values on the specified positions
        start                   (int)               Starting point (block) inside the bytearray
        end                     (int)               End point (block) inside the bytearray
        min                     (int)               Minimum byte used during flipping
        max                     (int)               Maximum byte used during flipping
        skipped                 (int)               Number of positions that should not be reached

    Returns:
            None
    '''
    cookie = ccm.CryptedCookie(cookie_sample)
    generator = cookie.flipping_generator(0, -1, start, stop, min, max)

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


def test_sample_probe():
    '''
    This sample matches the call:
        ccm MJEAhaGscNcK6zj0Tj13pocV1q6x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==
        --bit-flip --start-byte 16 --end-byte 21 --min-byte 250 --max-byte 255

    Paramaters:
        None

    Returns:
        None
    '''
    cookie = ccm.CryptedCookie(sample_1)
    generator = cookie.flipping_generator(16, 21, None, None, 250, 255)

    known_result = [
        'MJEAhaGscNcK6zj0Tj13pvoV1q6x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pvsV1q6x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pvwV1q6x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pv0V1q6x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pv4V1q6x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pv8V1q6x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pof61q6x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pof71q6x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pof81q6x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pof91q6x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pof+1q6x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pof/1q6x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pocV+q6x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pocV+66x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pocV/K6x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pocV/a6x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pocV/q6x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pocV/66x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pocV1vqx7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pocV1vux7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pocV1vyx7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pocV1v2x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pocV1v6x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pocV1v+x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pocV1q767IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pocV1q777IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pocV1q787IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pocV1q797IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pocV1q7+7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pocV1q7/7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pocV1q6x+oaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pocV1q6x+4aVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pocV1q6x/IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pocV1q6x/YaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pocV1q6x/oaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
        'MJEAhaGscNcK6zj0Tj13pocV1q6x/4aVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w==',
    ]

    for item in generator:
        assert item == known_result.pop(0)


@pytest.mark.parametrize('start, stop', [(56, 56), (56, 57), (57, 57), (60, 60)])
def test_out_of_bound(start, stop):
    '''
    Checks whether a flipping operation on the last block leads to an empty generator. Flipping
    the last block does not make sense and an empty generator is therefore expected.

    Paramaters:
        start               (int)               Start position inside the bytearray (byte)
        end                 (int)               End position inside the bytearray (byte)

    Returns:
        None
    '''
    cookie = ccm.CryptedCookie(sample_1)
    generator = cookie.flipping_generator(start, stop, None, None, 250, 255)

    assert next(generator, None) is None
