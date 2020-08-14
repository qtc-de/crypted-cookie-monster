#!/usr/bin/python3

import ccm
import pytest
import itertools


def j(b_list):
    '''
    Helper function that joins a list of strings into one string.

    Paramaters:
        b_list          (list[string])          List of strings to join

    Returns:
        result          (string)                Joined list
    '''
    return ''.join(b_list)


def jj(bb_list):
    '''
    Helper function that joins lists contained inside a list to a list of strings.

    Paramaters:
        bb_list         (list[list[string]])    List containing lists of strings

    Returns:
        result          (list[string])          Resulting list of strings
    '''
    result = []
    for b in bb_list:
        text = ''.join(b)
        result.append(text)

    return result


def full_shuffle(b_8, b_16):
    '''
    Creates a full shuffle from the given block lists.

    Paramaters:
        b_8             (list[string])          List of 8 byte blocks from the sample
        b_16            (list[string])          List of 16 byte blocks from the sample

    Returns:
        result          (list[string])          List of shuffled blocks
    '''
    full_shuffle = []
    for ctr in range(len(b_8)):

        block_list = b_8.copy()
        block = block_list.pop(ctr)

        for cts in range(len(b_8)):
            copy = block_list.copy()
            copy.insert(cts, block)

            cookie = ''
            for item in copy:
                cookie += item

            full_shuffle.append(cookie)

    for ctr in range(len(b_16)):

        block_list = b_16.copy()
        block = block_list.pop(ctr)

        for cts in range(len(b_16)):
            copy = block_list.copy()
            copy.insert(cts, block)

            cookie = ''
            for item in copy:
                cookie += item

            full_shuffle.append(cookie)

    return list(filter(lambda x: x != sample_hex, full_shuffle))


sample_hex = '30910085a1ac70d70aeb38f44e3d77a68715d6aeb1ec869553401d909'
sample_hex += 'f219c765711f5c7a434d4f0f9fc0481fb8950594736fc344b00d41032bf148d8e3349d7'

b_8 = [
        '30910085a1ac70d7',
        '0aeb38f44e3d77a6',
        '8715d6aeb1ec8695',
        '53401d909f219c76',
        '5711f5c7a434d4f0',
        'f9fc0481fb895059',
        '4736fc344b00d410',
        '32bf148d8e3349d7',
]

b_16 = [
        '30910085a1ac70d70aeb38f44e3d77a6',
        '8715d6aeb1ec869553401d909f219c76',
        '5711f5c7a434d4f0f9fc0481fb895059',
        '4736fc344b00d41032bf148d8e3349d7',
]


shuffle_format = 'cookie_sample, start, end, target_blocks, keep, result'
shuffle_samples = [
        (sample_hex, 0, 1, [3], False, [
            b_8[3] + j(b_8[0:3]) + j(b_8[4:]),
            b_8[0] + b_8[3] + j(b_8[1:3]) + j(b_8[4:]),
            b_16[3] + j(b_16[0:3]),
            b_16[0] + b_16[3] + j(b_16[1:3])]),

        (sample_hex, 0, 1, [3], True, [
            b_8[3] + j(b_8[0:]),
            b_8[0] + b_8[3] + j(b_8[1:]),
            b_16[3] + j(b_16[0:]),
            b_16[0] + b_16[3] + j(b_16[1:])]),

        (sample_hex, 2, 3, [0, 1], False, [
            j(b_8[1:3]) + b_8[0] + j(b_8[3:]),
            j(b_8[1:4]) + b_8[0] + j(b_8[4:]),
            j(b_16[1:3]) + b_16[0] + b_16[3],
            j(b_16[1:4]) + b_16[0],

            b_8[0] + b_8[2] + b_8[1] + j(b_8[3:]),
            b_8[0] + j(b_8[2:4]) + b_8[1] + j(b_8[4:]),
            b_16[0] + b_16[2] + b_16[1] + b_16[3],
            b_16[0] + j(b_16[2:4]) + b_16[1]]),

        (sample_hex, 2, 3, [0, 1], True, [
            j(b_8[0:2]) + b_8[0] + j(b_8[2:]),
            j(b_8[0:3]) + b_8[0] + j(b_8[3:]),
            j(b_16[0:2]) + b_16[0] + j(b_16[2:]),
            j(b_16[0:3]) + b_16[0] + b_16[3],

            j(b_8[0:2]) + b_8[1] + j(b_8[2:]),
            j(b_8[0:3]) + b_8[1] + j(b_8[3:]),
            j(b_16[0:2]) + b_16[1] + j(b_16[2:]),
            j(b_16[0:3]) + b_16[1] + b_16[3]]),

        (sample_hex, None, None, None, False, full_shuffle(b_8, b_16)),
        (sample_hex, 0, -1, None, False, full_shuffle(b_8, b_16)),
        (sample_hex, -1, None, None, False, full_shuffle(b_8, b_16))
]

full_shuffle_format = 'cookie_sample, start, end, result'
full_shuffle_samples = [
        (sample_hex, 0, 1, [
            j(b_8),
            b_8[1] + b_8[0] + j(b_8[2:]),
            j(b_16),
            b_16[1] + b_16[0] + j(b_16[2:])]),

        (sample_hex, 2, 3, [
            j(b_8),
            j(b_8[0:2]) + b_8[3] + b_8[2] + j(b_8[4:]),
            j(b_16),
            j(b_16[0:2]) + b_16[3] + b_16[2]]),

        (sample_hex, 1, 3, [
            b_8[0] + b_8[1] + b_8[3] + b_8[2] + j(b_8[4:]),
            b_8[0] + b_8[1] + b_8[2] + b_8[3] + j(b_8[4:]),
            b_8[0] + b_8[2] + b_8[3] + b_8[1] + j(b_8[4:]),
            b_8[0] + b_8[2] + b_8[1] + b_8[3] + j(b_8[4:]),
            b_8[0] + b_8[3] + b_8[1] + b_8[2] + j(b_8[4:]),
            b_8[0] + b_8[3] + b_8[2] + b_8[1] + j(b_8[4:]),
            b_16[0] + b_16[1] + b_16[2] + b_16[3],
            b_16[0] + b_16[1] + b_16[3] + b_16[2],
            b_16[0] + b_16[2] + b_16[3] + b_16[1],
            b_16[0] + b_16[2] + b_16[1] + b_16[3],
            b_16[0] + b_16[3] + b_16[1] + b_16[2],
            b_16[0] + b_16[3] + b_16[2] + b_16[1]]),

        (sample_hex, -1, -1, jj(itertools.permutations(b_8)) + jj(itertools.permutations(b_16)))
]


@pytest.mark.parametrize(shuffle_format, shuffle_samples)
def test_shuffeling(cookie_sample, start, end, target_blocks, keep, result):
    '''
    Performs a shuffle operation and checks whether the result has the expected outcome.

    Parameters:
        cookie_sample           (string)            Cookie sample value in b64
        start                   (int)               Left boundary where blocks will be moved
        end                     (int)               Right boundary where blocks will be moved
        target_blocks           (list[int])         List with indices of blocks that should be moved
        keep                    (boolean)           Decides whether moved blocks are kept in their original position too
        result                  (list[string])      Expected result

    Returns:
        None
    '''
    cookie = ccm.CryptedCookie(cookie_sample)
    generator = cookie.shuffeling_generator(start=start, end=end, target_blocks=target_blocks, keep=keep)

    for item in generator:
        result.remove(item)

    assert len(result) == 0


@pytest.mark.parametrize(full_shuffle_format, full_shuffle_samples)
def test_full_shuffeling(cookie_sample, start, end, result):
    '''
    Performs a shuffle operation and checks whether the result has the expected outcome.

    Parameters:
        cookie_sample           (string)            Cookie sample value in b64
        start                   (int)               Left boundary where blocks will be shuffled
        end                     (int)               Right boundary where blocks will be shuffled
        result                  (list[string])      Expected result

    Returns:
        None
    '''
    cookie = ccm.CryptedCookie(cookie_sample)
    generator = cookie.full_shuffeling_generator(start=start, end=end)

    for item in generator:
        result.remove(item)

    assert len(result) == 0
