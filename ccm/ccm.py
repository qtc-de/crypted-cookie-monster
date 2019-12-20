import re
import sys
import base64
import binascii
import itertools
from urllib.parse import unquote, quote


class Crypted_cookie:
    '''
    The crypted_cookie class is used to represent an encrypted cookie. Apart from the actual value, 
    it stores meta information about the cookie like its blocksize, encoding and format. All functions
    defined in this class (apart from __init__) require a valid Crypted_cookie object to work with. 
    On the one hand this makes the class less flexible for general use cases, but on the other hand
    it simplifies a lot of code that is used for the intentional purpose.
    '''


    def __init__(self, cookie_value, block_sizes=None, cookie_format=None, cookie_bytearray=None):
        '''
        Creates a Crypted_cookie object. If no blocksize, cookie_format or cookie_bytearray values
        are speicifed, all of them are automatically set during the initialisation procedure.

        Paramaters:
            block_sizes                 (list[int])         List of possible blocksizes
            cookie_format               (String)            Either hex or b64
            cookie_bytearray            (bytearray)         The decoded cookie value as bytearray

        Returns:
            crypted_cookie              (Crypted_cookie)    A Crypted_cookie object
        '''
        self.websafe = False
        self.url_encoded = False
        self.cookie_value = cookie_value
        self.cookie_format = cookie_format
        self.cookie_bytearray = self.decode_cookie()
        self.block_sizes = block_sizes if block_sizes else self.block_sizes()


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
            self.cookie_bytearray       Is set to the bytearray representation of self.cookie_value
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

        return None


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
        if cookie_bytearray == None:
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

        return None


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
        (start, end) = self.start_and_end(start_byte, end_byte, start_block, end_block)
        if start == None or end == None :
            return
        
        if lowest == None:
            lowest = 0
        if highest == None:
            highest = 255

        if lowest >= highest:
            return

        for i in range(start, end):
            for j in range(lowest, highest):
                modified_bytearray = self.cookie_bytearray.copy()
                modified_bytearray[i] = j
                cookie_value = self.encode_cookie(modified_bytearray)
                yield cookie_value


    def aimed_flipping_generator(self, current_name, desired_name, start_byte=None, end_byte=None, start_block=None, end_block=None):
        '''
        In contrast to the ordinary 'flipping_generator' function, which just flips each bit inside the desired flipping
        range, this function flips a group of bits/bytes in order to deterministically change a larger portion of characters
        inside the decrypted cookie value.

        Parameters:
            current_name        (String)        The string that you want to modify inside the encrypted cookie
            desired_name        (String)        The desired value in which 'current_name' should be flipped to
            start_byte          (int)           Start position inside self.cookie_bytearray for the bitflippling process
            end_byte            (int)           End position inside self.cookie_bytearray for the bitflippling process
            start_block         (int)           Block number where the bitflippling process should start from
            end_block           (int)           Block number where the bitflippling process should end

        Returns:
            gen                 (generator)     A generator object that provides a bitflipped cookie_value on each iteration
        '''
        length = len(desired_name)

        (start, end) = self.start_and_end(start_byte, end_byte, start_block, end_block)
        if start == None or end == None :
            return

        if len(current_name) != length:
            return

        current_bytearray = bytearray(current_name, "utf-8")
        desired_bytearray = bytearray(desired_name, "utf-8")
        xored_bytearray = bytearray(length)
        for i in range(length):
            xored_bytearray[i] = current_bytearray[i] ^ desired_bytearray[i]


        for blocksize in self.block_sizes:
            start_block = start // blocksize
            end_block = end // blocksize
            blocks = self.get_blocks(blocksize)
            block_count = len(blocks)

            for i in range(start_block, end_block):
                for j in range(blocksize - length):
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
        length = len(self.cookie_bytearray)
        
        for blocksize in self.block_sizes:

            if length < 2 * blocksize:
                print("[-] Error! Padding checks require a cookie with at least the doubled blocksize.")
                return

            for i in range(0, 255):
                modified_bytearray = self.cookie_bytearray.copy()
                modified_bytearray[-blocksize-1] = i
                cookie_value = self.encode_cookie(modified_bytearray)
                yield cookie_value


    def shuffeling_generator(self):
        '''
        Returns a generator that provied payload for attacking ECB block shuffeling. Currently this is not
        implemented very smart and I just included it because this implementation was quite easy. However, 
        it will be improved in future.

        Parameters:
            None

        Returns:
            gen             (generator)         Generator that returns ECB-block-shuffled cookie values
        '''
        for blocksize in self.block_sizes:

            blocks = self.get_blocks(blocksize)
            for permu in itertools.permutations(blocks):
                cookie_value = bytearray()
                for item in permu:
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
        for i in range(0, len(self.cookie_bytearray), blocksize):
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
        number_of_bytes = len(self.cookie_bytearray)

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
        number_of_bytes = len(self.cookie_bytearray)
        print(f"[+] Cookie Size: {str(number_of_bytes)}")

        valid = False
        for i in self.block_sizes:
            
            print(f"[+] Possible block length: {i}")
            valid = True

        if not valid:
            print(f"[-] Cookie seems not to be encrypted by a known block-cipher")


    def start_and_end(self, start_byte, end_byte, start_block, end_block):
        '''
        This is basically a sanity check that is done when a user submits the starting/ending position
        for an attack. It just checks if the specified values are in range of the cookie length and 
        if start is smaller than end and so on. Additionally, it will clear situations where the user
        has specified both, a byte position and a block position. In these situations the block position
        gets preferred. 

        Parameters: 
            start_byte          (int)               Start position inside self.cookie_bytearray
            end_byte            (int)               End position inside self.cookie_bytearray
            start_block         (int)               Block number where to start from
            end_block           (int)               Block number where to end

        Returns
            (start, end)        (tuple(int,int))    Sanitized values for starting and ending positions
        '''
        length = len(self.cookie_bytearray)
        min_size = min(self.block_sizes)

        # if the start byte was not set or is smaller than zero, we start from the beginning.
        if start_byte == None or start_byte < 0:
            start = 0

        # if a start byte was set and it is located before the last block, we start from this byte.
        elif start_byte < (length - min_size):
            start = start_byte

        # in all other cases, we set the start to the first byte of the last block (deadend).
        else:
            start = length - min_size

        # if not end byte was provided, the end byte is lower than zero or greater than the actual bytearray
        # length, we take the beginning of the last block as end.
        if end_byte == None or end_byte < 0 or end_byte > (length - min_size):
            end = length - min_size

        # otherwise, we use the specified end byte as the end.
        else:
            end = end_byte

        if start_block:

            # if the start block is smaller than zero, we start from zero.
            if start_block < 0:
                start = 0

            # if the start block is located before the last block, we use it as start.
            elif start_block < (length // min_size):
                start = start_block * min(self.block_sizes)

            # othwerwise we start on the first byte of the last block (deadend).
            else:
                start = length - min_size

        if end_block:

            # if the end block is smaller than zero or greater equal the second last block, we set
            # the end to the first byte of the last block.
            if end_block < 0 or end_block >= (length // min_size - 1):
                end = length - min_size

            # otherwise we use the specified end block as the end.
            else:
                end = (end_block + 1) * min(self.block_sizes)

        if start >= end:
            return (None, None)

        return (start, end)
