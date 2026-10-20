import re
import struct
import itertools
import sys

def is_zip_bomb(filename):
    with open(filename, "rb") as f:
        zip_content = f.read()
        # return True if it is a zip bomb
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
