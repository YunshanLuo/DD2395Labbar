import pyzipper
import os
import sys
import argparse

def compute_size(zip_path, chunk_size=32 * 1024 * 1024):  # 32MB chunk size
    total_read = 0

    compressed_size = os.path.getsize(zip_path)
    print(f"Zipped size: {format_file_size(compressed_size)}")

    try:
        # Open the zip
        with pyzipper.AESZipFile(zip_path, 'r') as zf:
            # Loop through each file in the zip
            for file_info in zf.infolist():
                print(file_info)
                # Open the file for reading
                with zf.open(file_info, 'r') as file:
                    # Read file in chunks
                    while True:
                        chunk = file.read(chunk_size)
                        if not chunk:
                            break

                        # Keep track of size and discarding the data)
                        total_read += len(chunk)

                        display_progress(total_read, compressed_size)
        print()
        print("Successfully finished unzipping")
    except (pyzipper.BadZipFile, pyzipper.LargeZipFile) as e:
        print(f"Error: Bad zip file or too large to process - {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    return (compressed_size, total_read)

def display_progress(total_read, compressed_size):
    compression_ratio = total_read / compressed_size if compressed_size > 0 else 1

    total_read_str = format_file_size(total_read)
    compression_ratio_str = format_large_number(compression_ratio)

    sys.stdout.write(f'\rUnpacking: {total_read_str}, Compression ratio: {compression_ratio_str}    ')
    sys.stdout.flush()

def format_file_size(bytes):
    if bytes < 1024:
        return f"{bytes} B"
    elif bytes < 1024 ** 2:
        return f"{bytes / 1024:.2f} KB"
    elif bytes < 1024 ** 3:
        return f"{bytes / 1024 ** 2:.2f} MB"
    else:
        return f"{bytes / 1024 ** 3:.2f} GB"

def format_large_number(num):
    """Formats a number to 1-999, 1k-999k, 1m+ with one decimal point."""
    if num < 1000:
        return f'{num:.1f}'  # No suffix, display 1-999 with one decimal
    elif num < 1_000_000:
        return f'{num / 1_000:.1f}k'  # 1k-999k
    else:
        return f'{num / 1_000_000:.1f}m'  # 1m+

def extract_content(zip_path, file_path, chunk_size=32 * 1024 * 1024):  # 32MB chunk size
    unzip_data = bytearray()
    # Open the zip
    with pyzipper.AESZipFile(zip_path, 'r') as zf:
        # Loop through each file in the zip
        for file_info in zf.infolist():
            if not(file_info.filename == file_path):
                continue
            # Open the file for reading
            with zf.open(file_info, 'r') as file:
                # Read file in chunks
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break
                    unzip_data.extend(chunk)
    return(unzip_data)

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Unzip a file and display progress.")
    parser.add_argument('zip_file', help="Path to the zip file to unzip")

    # Parse the arguments
    args = parser.parse_args()

    # Call the process_zip function with the specified zip file
    compute_size(args.zip_file)

if __name__ == "__main__":
    main()
