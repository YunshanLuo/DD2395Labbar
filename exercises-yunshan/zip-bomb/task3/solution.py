import re
import struct
import itertools
import sys

def is_zip_bomb(filename):
    with open(filename, "rb") as f:
        zip_content = f.read()

        # parse central directory headers and check if multiple
        # files point to overlapping data regions
        cdh_sig = struct.pack('<I', 0x02014b50)
        lfh_sig = struct.pack('<I', 0x04034b50)

        # find all CDH entries and extract their local header offsets
        local_offsets = []
        pos = 0
        while True:
            idx = zip_content.find(cdh_sig, pos)
            if idx == -1:
                break
            # local file header offset is at byte 42 from the CDH signature
            offset = struct.unpack_from('<I', zip_content, idx + 42)[0]
            local_offsets.append(offset)
            pos = idx + 46  # move past this CDH

        # if there are fewer than 2 files it cant really be a bomb
        if len(local_offsets) < 2:
            return False

        # check if any compressed data regions overlap
        # for each local file header, figure out where the data starts and ends
        data_ranges = []
        for offset in local_offsets:
            if zip_content[offset:offset+4] != lfh_sig:
                continue
            fname_len = struct.unpack_from('<H', zip_content, offset + 26)[0]
            extra_len = struct.unpack_from('<H', zip_content, offset + 28)[0]
            comp_size = struct.unpack_from('<I', zip_content, offset + 18)[0]
            data_start = offset + 30 + fname_len + extra_len
            data_end = data_start + comp_size
            data_ranges.append((data_start, data_end))

        # check for overlapping ranges - a sign of a zip bomb
        for i in range(len(data_ranges)):
            for j in range(i+1, len(data_ranges)):
                start_i, end_i = data_ranges[i]
                start_j, end_j = data_ranges[j]
                # check if the ranges share any bytes
                if start_i < end_j and start_j < end_i:
                    return True

        return False

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Check if the zip file is a bomb")
    parser.add_argument('zip_file', help="Path to the zip file to check")

    # Parse the arguments
    args = parser.parse_args()

    # Call the process_zip function with the specified zip file
    if is_zip_bomb(args.zip_file):
        print("Bomb detected")
    else:
        print("Safe file")

if __name__ == "__main__":
    main()
