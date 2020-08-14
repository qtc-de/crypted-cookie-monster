import base64
import binascii
import itertools
from urllib.parse import unquote, quote


class CcmException(Exception):
    '''
    Custom exception class.
    '''


def verify_blocksize(block_sizes):
    '''
    Verifies that the block_sizes list contains only the values 8 and/or 16.

    Paramaters:
        block_sizes                     (list[int])         List of possible blocksizes

    Returns:
        None
    '''
    for block_size in block_sizes:
        if block_size != 8 and block_size != 16:
            raise CcmException(f"Invalid blocksize '{block_size}'.")


class CryptedCookie:
    '''
    The crypted_cookie class is used to represent an encrypted cookie. Apart from the actual value,
    it stores meta information about the cookie like its blocksize, encoding and format. All functions
    defined in this class (apart from __init__) require a valid CryptedCookie object to work with.
    On the one hand this makes the class less flexible for general use cases, but on the other hand
    it simplifies a lot of code that is used for the intentional purpose.
    '''

    def __init__(self, cookie_value, block_sizes=None, cookie_format=None, cookie_bytearray=None):
        '''
        Creates a CryptedCookie object. If no blocksize, cookie_format or cookie_bytearray values
        are speicifed, all of them are automatically set during the initialisation procedure.

        Paramaters:
            block_sizes                 (list[int])         List of possible blocksizes
            cookie_format               (String)            Either hex or b64
            cookie_bytearray            (bytearray)         The decoded cookie value as bytearray

        Returns:
            crypted_cookie              (CryptedCookie)    A CryptedCookie object
        '''
        self.websafe = False
        self.url_encoded = False
        self.cookie_value = cookie_value
        self.cookie_format = cookie_format
        self.cookie_bytearray = self.decode_cookie()
        self.cookie_length = len(self.cookie_bytearray)
        self.block_sizes = block_sizes if block_sizes else self.block_sizes()
        verify_blocksize(self.block_sizes)

    def decode_cookie(self):
        '''
        Uses the value of the self.cookie_value property and decodes the corresponding data
        into a bytearray. For decoding, ccm either uses the user supplied format or it tries
        to determine the format on its own.

        Parameters:
            None

        Returns:
            None

        Side-Effects:
            self.websafe                Is set when the cookie seems to be websafe encoded
            self.url_encoded            Is set when the cookie seems to be url encoded
            self.cookie_format          If not present before, it gets set to the determined format
        '''
        if not self.cookie_format == 'b64':

            try:
                cookie_bytearray = bytearray.fromhex(self.cookie_value)
                self.cookie_format = 'hex'
                return cookie_bytearray
            except ValueError:
                pass

        if not self.cookie_format == 'hex':

            try:
                cookie_value_p = unquote(self.cookie_value)

                if cookie_value_p != self.cookie_value:
                    self.url_encoded = True

                cookie_value_r = cookie_value_p.replace('_', '/')
                cookie_value_r = cookie_value_p.replace('-', '+')

                if cookie_value_r != cookie_value_p:
                    self.websafe = True

                cookie_bytearray = base64.b64decode(cookie_value_r)
                cookie_bytearray = bytearray(cookie_bytearray)
                self.cookie_format = 'b64'
                return cookie_bytearray

            except binascii.Error:
                pass

        raise CcmException("decode_cookie(... - Cookie value seems neither hex nor base64 encoded.")

    def encode_cookie(self, cookie_bytearray=None):
        '''
        The inverse operation to 'decode_cookie'. It uses the saved format information
        (like websafe, url_encode, b64, ...) from the cookie to convert the self.cookie_bytearray
        value back to the original format. The function does also allow to specify a
        different cookie_bytearray that should be encoded, because during a wordlist generation
        you want to create different cookie values based on the original input cookie.

        Paramaters:
            cookie_bytearray            (bytearray)         Optional bytearray that will be encoded

        Returns
            cookie_value                (String)            UTF-8 encoded cookie value
        '''
        if cookie_bytearray is None:
            cookie_bytearray = self.cookie_bytearray

        if not self.cookie_format == 'b64':

            cookie_value = cookie_bytearray.hex()
            return cookie_value

        if not self.cookie_format == 'hex':

            cookie_value = base64.b64encode(cookie_bytearray)
            cookie_value = cookie_value.decode('utf-8')

            if self.websafe:
                cookie_value = cookie_value.replace('/', '_')
                cookie_value = cookie_value.replace('+', '-')

            if self.url_encoded:
                cookie_value = quote(cookie_value)

            return cookie_value

        raise CcmException("encode_cookie(... - Cookie object contains no valid format information (hex|b64).")

    def flipping_generator(self, start_byte=None, end_byte=None, start_block=None, end_block=None, lowest=None, highest=None):
        '''
        Flips bytes inside of the self.cookie_bytearray property and yields the encoded cookie representation.
        Thus, this function creates a generator that yields a differently positioned bit-flip on each iteration.

        Parameters:
            start_byte          (int)           Start position inside self.cookie_bytearray for the bitflippling process
            end_byte            (int)           End position inside self.cookie_bytearray for the bitflippling process
            start_block         (int)           Block number where the bitflippling process should start from
            end_block           (int)           Block number where the bitflippling process should end
            lowest              (int)           Lowest byte number that is inserted during the flipping process
            highest             (int)           Highest byte number that is inserted during the flipping process

        Returns:
            gen                 (generator)     A generator object that provides a bitflipped cookie_value on each iteration
        '''
        max_length = self.cookie_length - min(self.block_sizes)
        (start, end) = self.start_and_end(start_byte, end_byte, start_block, end_block, min(self.block_sizes))

        if (start >= max_length):
            return

        if (end >= max_length):
            end = max_length - 1

        if lowest is None:
            lowest = 0
        if highest is None:
            highest = 255

        if lowest > highest:
            return

        for i in range(start, end + 1):
            for j in range(lowest, highest + 1):

                if self.cookie_bytearray[i] == j:
                    continue

                modified_bytearray = self.cookie_bytearray.copy()
                modified_bytearray[i] = j

                cookie_value = self.encode_cookie(modified_bytearray)
                yield cookie_value

    def aimed_flipping_generator(self, current, desired, start_byte=None, end_byte=None, start_block=None, end_block=None):
        '''
        In contrast to the ordinary 'flipping_generator' function, which just flips each bit inside the desired flipping
        range, this function flips a group of bits/bytes in order to deterministically change a larger portion of characters
        inside the decrypted cookie value.

        Parameters:
            current             (String)        The string that you want to modify inside the encrypted cookie
            desired             (String)        The desired value in which 'current_name' should be flipped to
            start_byte          (int)           Start position inside self.cookie_bytearray for the bitflippling process
            end_byte            (int)           End position inside self.cookie_bytearray for the bitflippling process
            start_block         (int)           Block number where the bitflippling process should start from
            end_block           (int)           Block number where the bitflippling process should end

        Returns:
            gen                 (generator)     A generator object that provides a bitflipped cookie_value on each iteration
        '''
        length = len(desired)

        if len(current) != length:
            raise CcmException("aimed_flipping_generator(... - 'current' and 'desired' need to be of the same length.")

        current_bytearray = bytearray(current, "utf-8")
        desired_bytearray = bytearray(desired, "utf-8")

        xored_bytearray = bytearray(length)
        for i in range(length):
            xored_bytearray[i] = current_bytearray[i] ^ desired_bytearray[i]

        for blocksize in self.block_sizes:

            (start, end) = self.start_and_end(start_byte, end_byte, start_block, end_block, blocksize, 'block')

            blocks = self.get_blocks(blocksize)
            block_count = len(blocks)

            for i in range(start, end + 1):
                for j in range(blocksize - length + 1):
                    modified_block = blocks[i].copy()
                    for k in range(length):
                        modified_block[j + k] = xored_bytearray[k] ^ modified_block[j + k]

                    cookie_value = bytearray()
                    for k in range(block_count):
                        if k != i:
                            cookie_value += blocks[k]
                        else:
                            cookie_value += modified_block

                    cookie_value = self.encode_cookie(cookie_value)

                    yield cookie_value

    def padding_generator(self):
        '''
        Just flips the last byte inside the second last block in order to violate the correct block padding.
        This can be used to quickly identify padding oracles. If an application is vulnerable, it should
        return between two and three unqiue answers during this wordlist attack.

        Parameters:
            None

        Returns:
            gen             (generator)             Generator that returns a padding-modified cookie_value
        '''
        length = self.cookie_length

        for blocksize in self.block_sizes:

            if length < 2 * blocksize:
                print("[-] Error! Padding checks require a cookie with at least the doubled blocksize.")
                return

            for i in range(0, 255 + 1):
                modified_bytearray = self.cookie_bytearray.copy()
                modified_bytearray[-blocksize-1] = i
                cookie_value = self.encode_cookie(modified_bytearray)
                yield cookie_value

    def shuffeling_generator(self, start=None, end=None, target_blocks=None, keep=False):
        '''
        Takes a block (or multiple blocks) from the encrypted sample and changes the position inside the
        block array. This can be used to attack ECB ciphers. The amount of blocks being moved can be controlled
        by the 'target_blocks' paramater. The positions where the blocks are going to be moved can be controlled
        by using the 'start' and 'stop' paramaters. Indizes specified for these values determine the index position
        in the final shuffled result. E.g. end=4 means, that the target_block will have the index 4 in the final
        shuffled block array. Moved blocks are really 'moved' and do not appear twice in the block array after the
        movement. If you want to keep the original block position, use the 'keep' paramater.

        Parameters:
            start           (int)               Left boundary where blocks will be moved
            end             (int)               Right boundary where blocks will be moved
            target_blocks   (list[int])         List with indices of blocks that should be moved
            keep            (boolean)           Decides whether moved blocks are kept in their original position too

        Returns:
            gen             (generator)         Generator that returns ECB-block-shuffled cookie values
        '''
        for blocksize in self.block_sizes:

            blocks = self.get_blocks(blocksize)
            block_count = len(blocks)

            start_value, end_value = self.start_and_end(None, None, start, end, block_size=blocksize, output='block')
            if keep and (end is None or end >= block_count or end < 0):
                end_value = block_count

            blocks_to_move = range(0, block_count)
            if target_blocks:
                blocks_to_move = target_blocks

            for block_index in blocks_to_move:
                if block_index >= block_count:
                    raise CcmException(f"shuffeling_generator(... - Specified target block '{block_index}' is out of range.")

                for ctr in range(start_value, end_value + 1):

                    if ctr == block_index:
                        continue

                    cookie_value = bytearray()
                    block_list = blocks.copy()

                    if not keep:
                        del block_list[block_index]

                    block_list.insert(ctr, blocks[block_index])
                    for item in block_list:
                        cookie_value += item

                    cookie_value = self.encode_cookie(cookie_value)
                    yield cookie_value

    def full_shuffeling_generator(self, start=None, end=None):
        '''
        The 'shuffeling_generator' function only moves one block in each sample. All other blocks are untouched.
        The 'full_shuffeling_generator' returns all possible permutations inside the start<->stop area instead.

        Parameters:
            start            (int)               First block to include in the shuffling process
            end              (int)               Last block to include in the shuffling process

        Returns:
            gen             (generator)         Generator that returns ECB-block-shuffled cookie values
        '''
        for blocksize in self.block_sizes:

            blocks = self.get_blocks(blocksize)
            block_count = len(blocks)

            start, end = self.start_and_end(None, None, start, end, block_size=blocksize, output='block')

            prefix_blocks = blocks[0:start]
            suffix_blocks = []

            if end != block_count - 1:
                suffix_blocks = blocks[end + 1:]

            permu_blocks = blocks[start:end + 1]

            for permu in itertools.permutations(permu_blocks):

                cookie_value = bytearray()
                for item in prefix_blocks:
                    cookie_value += item

                for item in permu:
                    cookie_value += item

                for item in suffix_blocks:
                    cookie_value += item

                cookie_value = self.encode_cookie(cookie_value)
                yield cookie_value

    def get_blocks(self, blocksize=8):
        '''
        Small helper function that just returns a list of bytearrays for each block inside self.cookie_bytearray.

        Parameters:
            blocksize       (int)               Desired size of the bytearray blocks

        Returns:
            blocks          (list[bytearray])   List of bytearray blocks
        '''
        blocks = []
        for i in range(0, self.cookie_length, blocksize):
            blocks.append(self.cookie_bytearray[i:i+blocksize])
        return blocks

    def block_sizes(self):
        '''
        Just uses the length of self.cookie_bytearray to determine possible blocksizes.

        Paramaters:
            None

        Returns:
            possible_sizes      (list[int])     List of possible block sizes
        '''
        possible_sizes = []
        number_of_bytes = self.cookie_length

        if number_of_bytes % 8 == 0 and number_of_bytes >= 2 * 8:
            possible_sizes.append(8)
        if number_of_bytes % 16 == 0 and number_of_bytes >= 2 * 16:
            possible_sizes.append(16)
        return possible_sizes

    def print_info(self):
        '''
        Just prints some general information about the cookie.

        Paramaters:
            None

        Returns:
            None
        '''
        number_of_bytes = self.cookie_length
        print(f"[+] Cookie Size: {str(number_of_bytes)}")

        valid = False
        for i in self.block_sizes:

            print(f"[+] Possible block length: {i} \t({number_of_bytes // i} blocks)")
            valid = True

        if not valid:
            print("[-] Cookie seems not to be encrypted by a known block-cipher")

    def get_start_byte(self, start_byte):
        '''
        Sanity check if the specified start byte is inside the byte range of the encrypted
        sample. Furthermore, some special values get replaced by their corresponding offset.
        The start_byte parameter is expected as the index inside the bytearray. It is also
        returned as an index. E.g. if the specified start_byte is greater than the bytearray
        length, {length - 1} is returned.

        Parameters:
            start_byte          (int)               Start position inside self.cookie_bytearray

        Returns
            start_byte          (int)               Validated and maybe modified value of start_byte
        '''
        length = self.cookie_length

        if (start_byte is None) or (start_byte < 0):
            return 0

        elif start_byte >= length:
            return length - 1

        else:
            return start_byte

    def get_end_byte(self, end_byte):
        '''
        Sanity check if the specified end byte is inside the byte range of the encrypted
        sample. Furthermore, some special values get replaced by their corresponding offset.
        The end_byte parameter is expected as the index inside the bytearray. It is also
        returned as an index. E.g. if the specified end_byte is greater than the bytearray
        length, {length - 1} is returned.

        Parameters:
            end_byte            (int)               End position inside self.cookie_bytearray

        Returns
            end_byte            (int)               Validated and maybe modified value of end_byte
        '''
        length = self.cookie_length

        if (end_byte is None) or (end_byte < 0):
            return length - 1

        elif end_byte >= length:
            return length - 1

        else:
            return end_byte

    def get_start_block(self, start_block, block_size=None):
        '''
        Sanity check if the specified start_block is inside the byte range of the encrypted
        sample. Furthermore, some special values get replaced by their corresponding offset.
        The start_block parameter is expected as the index inside the bytearray. It is also
        returned as an index. E.g. if the specified start_block is greater than the bytearray
        length, {block_count - 1} is returned.

        Parameters:
            start_block         (int)               Start block inside self.cookie_bytearray
            block_size          (int)               Block size to use

        Returns
            start_block         (int)               Validated and maybe modified value of start_block
        '''
        if not block_size:
            block_size = min(self.block_sizes)

        count = self.cookie_length // block_size

        if (start_block is None) or (start_block < 0):
            return 0

        elif start_block >= count:
            return count - 1

        else:
            return start_block

    def get_end_block(self, end_block, block_size=None):
        '''
        Sanity check if the specified end_block is inside the byte range of the encrypted
        sample. Furthermore, some special values get replaced by their corresponding offset.
        The end_block parameter is expected as the index inside the bytearray. It is also
        returned as an index. E.g. if the specified end_block is greater than the bytearray
        length, {block_count - 1} is returned.

        Parameters:
            end_block           (int)               End block inside self.cookie_bytearray
            block_size          (int)               Block size to use

        Returns
            end_block           (int)               Validated and maybe modified value of end_block
        '''
        if not block_size:
            block_size = min(self.block_sizes)

        count = self.cookie_length // block_size

        if (end_block < 0) or (end_block >= count):
            return count - 1

        else:
            return end_block

    def start_and_end(self, start_byte, end_byte, start_block, end_block, block_size=8, output='byte'):
        '''
        Just a wrapper around start_end_byte and start_end_block. Chooses the corresponding
        function according to the specified arguments. start_byte and end_byte are used by default,
        unless the block values were specified. The output paramater specifies in which format output
        is reported, either as byte index or as block index.

        The value is always returned as the corresponding index in the bytearray (or as the index of
        the block in block mode). When specifying byte boundaries, but requesting block output, the
        values are rounded to the lower block bound.

        Paramaters:
            start_byte          (int)               Byte position to start from
            end_byte            (int)               Byte position to end on
            start_block         (int)               Block position to start from
            end_block           (int)               Block position to wnd from
            block_size          (int)               Blocksize to use
            output              (int)               Output format (byte|block)
        '''
        start = self.get_start_byte(start_byte)
        end = self.get_end_byte(end_byte)

        if start_block:
            start = self.get_start_block(start_block, block_size) * block_size
        if end_block:
            end = (self.get_end_block(end_block, block_size) + 1) * block_size - 1

        if start > end:
            raise CcmException(f"start_and_end(... - Start value '{start}' is greater than end value '{end}'.")

        if output == 'block':
            return (start // block_size, end // block_size)

        return (start, end)
