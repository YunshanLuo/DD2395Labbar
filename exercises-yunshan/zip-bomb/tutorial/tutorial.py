import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.commons import *

# Creates a small zip file
# Return: bytearray
def create_zip_file():
    uncompressed_data = b"File data to compress."
    # Create the file and its local file header
    compressed_data, size_compressed, size_uncompressed = compress_data(uncompressed_data)
    filename = "file1.txt"
    crc = zlib.crc32(uncompressed_data) & 0xffffffff
    lfh = create_lfh(filename, size_compressed, size_uncompressed, crc)

    # Writing to bytearray and creating CDH
    zip_file_data = bytearray()
    lfh_offset = len(zip_file_data) # This is 0 from the start
    zip_file_data.extend(lfh) # Insert LFH for kernel
    zip_file_data.extend(compressed_data)

    # Create CDH
    central_dir = bytearray()
    central_directory_offset = len(zip_file_data) # The byte offset from the beginning of the zip file to the beginning of the CDH:s

    # Offset for the kernel's LFH
    lfh_kernel_offset = lfh_offset
    cdh = create_cdh(filename, crc,
                            size_compressed,
                            size_uncompressed,
                            lfh_offset)
    central_dir.extend(cdh)

    # Add the CDH:s to the end of the LFH:s
    zip_file_data.extend(central_dir)

    # Create and add the 'end of central directory'
    eocd = create_eocd(len(central_dir), central_directory_offset, 1)
    zip_file_data.extend(eocd)

    with open("zip_file.zip", "wb") as f:
        f.write(zip_file_data)

if __name__ == "__main__":
    create_zip_file()
