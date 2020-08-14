#!/usr/bin/python3

import ccm
import pytest
import base64

sample = 'MJEAhaGscNcK6zj0Tj13pocV1q6x7IaVU0AdkJ8hnHZXEfXHpDTU8Pn8BIH7iVBZRzb8NEsA1BAyvxSNjjNJ1w=='
sample_bin = base64.b64decode(sample)
sample_length = len(sample_bin)
sample_blocks_8 = sample_length // 8
sample_blocks_16 = sample_length // 16

byte_offset_format = "sample_cookie, start, end, blocksize, type, expected_start, expected_end"
byte_offset_samples = [
        (sample, 0, -1, 8, 'byte', 0, sample_length - 1),
        (sample, 0, 50, 8, 'byte', 0, 50),
        (sample, 5, 50, 8, 'byte', 5, 50),
        (sample, 0, 90, 8, 'byte', 0, sample_length - 1),
        (sample, -1, -1, 8, 'byte', 0, sample_length - 1),

        (sample, 0, -1, 8, 'block', 0, sample_blocks_8 - 1),
        (sample, 0, 50, 8, 'block', 0, 6),
        (sample, 9, 50, 8, 'block', 1, 6),
        (sample, 16, 47, 8, 'block', 2, 5),
        (sample, 0, 90, 8, 'block', 0, sample_blocks_8 - 1),
        (sample, -1, -1, 8, 'block', 0, sample_blocks_8 - 1),

        (sample, 0, -1, 16, 'block', 0, sample_blocks_16 - 1),
        (sample, 0, 50, 16, 'block', 0, 3),
        (sample, 9, 50, 16, 'block', 0, 3),
        (sample, 16, 50, 16, 'block', 1, 3),
        (sample, 32, 47, 16, 'block', 2, 2),
        (sample, 0, 90, 16, 'block', 0, sample_blocks_16 - 1),
        (sample, -1, -1, 16, 'block', 0, sample_blocks_16 - 1),
]

block_offset_format = "sample_cookie, start, end, blocksize, type, expected_start, expected_end"
block_offset_samples = [
         (sample, 0, -1, 8, 'byte', 0, sample_length - 1),
         (sample, 0, 5, 8, 'byte', 0, 47),
         (sample, 5, 6, 8, 'byte', 40, 55),
         (sample, 0, 10, 8, 'byte', 0, sample_length - 1),
         (sample, -1, -1, 8, 'byte', 0, sample_length - 1),

         (sample, 0, -1, 8, 'block', 0, sample_blocks_8 - 1),
         (sample, 0, 6, 8, 'block', 0, 6),
         (sample, 2, 6, 8, 'block', 2, 6),
         (sample, 0, 10, 8, 'block', 0, sample_blocks_8 - 1),
         (sample, -1, -1, 8, 'block', 0, sample_blocks_8 - 1),

         (sample, 0, -1, 16, 'block', 0, sample_blocks_16 - 1),
         (sample, 0, 3, 16, 'block', 0, 3),
         (sample, 1, 2, 16, 'block', 1, 2),
         (sample, 0, 5, 16, 'block', 0, sample_blocks_16 - 1),
         (sample, -1, -1, 16, 'block', 0, sample_blocks_16 - 1),
]


@pytest.mark.parametrize(byte_offset_format, byte_offset_samples)
def test_byte_offsets(sample_cookie, start, end, blocksize, type, expected_start, expected_end):
    '''
    Tests if the start_and_end function calculates the correct offsets for the specified samples.

    Paramaters:
        sample_cookie           (string)                Sample cookie in b64 or hex
        start                   (int)                   Starting byte
        end                     (int)                   End byte
        blocksize               (int)                   Blocksize to use
        type                    (string)                Return type (either 'byte' or 'block')
        expected_start          (int)                   Result to expect for start
        expected_end            (int)                   Result to expect for end

    Returns:
        None
    '''
    cookie = ccm.CryptedCookie(sample_cookie)
    start, end = cookie.start_and_end(start, end, None, None, blocksize, type)

    assert start == expected_start
    assert end == expected_end


@pytest.mark.parametrize(block_offset_format, block_offset_samples)
def test_block_offsets(sample_cookie, start, end, blocksize, type, expected_start, expected_end):
    '''
    Tests if the start_and_end function calculates the correct offsets for the specified sampes

    Paramaters:
        sample_cookie           (string)                Sample cookie in b64 or hex
        start                   (int)                   Starting block
        end                     (int)                   End block
        blocksize               (int)                   Blocksize to use
        type                    (string)                Return type (either 'byte' or 'block')
        expected_start          (int)                   Result to expect for start
        expected_end            (int)                   Result to expect for end

    Returns:
        None
    '''
    cookie = ccm.CryptedCookie(sample_cookie)
    start, end = cookie.start_and_end(0, -1, start, end, blocksize, type)

    assert start == expected_start
    assert end == expected_end
