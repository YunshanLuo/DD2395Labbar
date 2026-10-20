import zlib
import struct
import time

def current_msdos_date_time():
    t = time.localtime()
    msdos_date = ((t.tm_year - 1980) << 9) | (t.tm_mon << 5) | t.tm_mday
    msdos_time = (t.tm_hour << 11) | (t.tm_min << 5) | (t.tm_sec // 2)
    return (msdos_date, msdos_time)

def compress_data(data):
    compressed_data = zlib.compress(data)[2:-4]
    compressed_data_size = len(compressed_data)
    uncompressed_data_size = len(data)

    return compressed_data, compressed_data_size, uncompressed_data_size


# LFH and CDH Constants
LFH_SIGNATURE = 0x04034b50
CDH_SIGNATURE = 0x02014b50
VERSION = 20
GENERAL_PURPOSE_BIT_FLAG = 0
COMPRESSION_METHOD = 8 # Deflate
EXTRA_FIELD_LENGTH = 0

#CDH specific constants
EXTRA_FIELD_LENGTH = 0
FILE_COMMENT_LENGTH = 0
DISK_NUMBER_START = 0
INTERNAL_FILE_ATTRIBUTES = 0
EXTERNAL_FILE_ATTRIBUTES = 0

#OCD specific constants
EOCD_SIGNATURE = 0x06054b50
NUMBER_OF_THIS_DISK = 0
DISK_WHERE_CENTRAL_DIR_STARTS = 0
ZIP_FILE_COMMENT_LEN = 0

def create_lfh(filename, compressed_size, uncompressed_size, crc):
    filename_encoded = filename.encode('utf-8')
    last_modification_date, last_modification_time = current_msdos_date_time()

    lfh = struct.pack(
        '<IHHHHHIIIHH',
        LFH_SIGNATURE,
        VERSION,
        GENERAL_PURPOSE_BIT_FLAG,
        COMPRESSION_METHOD,
        last_modification_time,
        last_modification_date,
        crc,
        compressed_size,
        uncompressed_size,
        len(filename_encoded),
        EXTRA_FIELD_LENGTH
    )
    return lfh + filename_encoded

def create_cdh(filename, crc, compressed_size, uncompressed_size, local_header_offset):
    filename_encoded = filename.encode('utf-8')
    last_modification_date, last_modification_time = current_msdos_date_time()
    cdh = struct.pack(
            '<IHHHHHHIIIHHHHHII',
            CDH_SIGNATURE,
            VERSION,
            VERSION,
            GENERAL_PURPOSE_BIT_FLAG,
            COMPRESSION_METHOD,
            last_modification_time,
            last_modification_date,
            crc,
            compressed_size,
            uncompressed_size,
            len(filename_encoded),
            EXTRA_FIELD_LENGTH,
            FILE_COMMENT_LENGTH,
            DISK_NUMBER_START,
            INTERNAL_FILE_ATTRIBUTES,
            EXTERNAL_FILE_ATTRIBUTES,
            local_header_offset
            )
    return cdh + filename_encoded

def create_eocd(central_dir_size, central_dir_offset, num_entries):
    return struct.pack(
            '<IHHHHIIH',
            EOCD_SIGNATURE,
            NUMBER_OF_THIS_DISK,
            DISK_WHERE_CENTRAL_DIR_STARTS,
            num_entries,
            num_entries,
            central_dir_size,
            central_dir_offset,
            ZIP_FILE_COMMENT_LEN
            )

# Non compressed block that specifies what data that should not be deflated
def create_non_compressed_block(data_len):
    block_len = data_len
    block_len_complement = 0xFFFF - block_len
    return struct.pack('<BHH', 0x00, block_len, block_len_complement)
