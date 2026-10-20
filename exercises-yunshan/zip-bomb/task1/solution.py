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

    with open("zip_bomb.zip", "wb") as f:
        f.write(zip_file_data)

if __name__ == "__main__":
    zip_bomb_data = create_zip_bomb()
