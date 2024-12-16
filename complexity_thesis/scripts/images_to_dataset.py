import argparse
import os
import requests
from PIL import Image
import pandas as pd

def download_images(csv_file, column, output_dir):
    """
    Downloads images from URLs provided in a specified CSV column.

    Args:
        csv_file (str): Path to the CSV file containing image URLs.
        column (str): Name of the column in the CSV file that contains URLs.
        output_dir (str): Directory where the downloaded images will be saved.

    Returns:
        list: A list of file paths for the successfully downloaded images.

    This function reads the URLs from the specified column of the input CSV file.
    Each URL is used to download an image, which is saved as a `.tif` file in the output directory.
    If a download fails, the error is logged, and the process continues for the remaining URLs.
    """
    os.makedirs(output_dir, exist_ok=True)  # Ensure the output directory exists.
    urls = pd.read_csv(csv_file)[column]  # Read the CSV file and extract the specified column.
    downloaded_files = []  # List to store paths of successfully downloaded files.

    for i, url in enumerate(urls):
        try:
            # Send an HTTP GET request to download the image.
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Raise an exception for HTTP errors.

            # Save the image with a sequential name.
            filename = os.path.join(output_dir, f"image_{i}.tif")
            with open(filename, "wb") as f:
                for chunk in response.iter_content(1024):  # Write the file in chunks for efficiency.
                    f.write(chunk)
            downloaded_files.append(filename)  # Add the successfully downloaded file to the list.
            print(f"Downloaded: {filename}")
        except Exception as e:
            print(f"Failed to download {url}: {e}")  # Log any errors during the download process.

    return downloaded_files

def convert_and_filter_images(input_files, output_dir, compression_level=6, min_side=512, max_pixels=768**2):
    """
    Converts .tif images to .png format, applies compression, and filters images by size.

    Args:
        input_files (list): List of file paths to the downloaded .tif images.
        output_dir (str): Directory where the processed .png images will be saved.
        compression_level (int): PNG compression level (0 = no compression, 9 = max compression).
        min_side (int): Minimum allowed size of the smaller side of the image.
        max_pixels (int): Maximum allowed total number of pixels (width * height).

    Returns:
        list: A list of file paths for the successfully processed and valid images.

    This function processes each `.tif` file:
    1. Checks if the image dimensions meet the specified criteria.
    2. Converts valid images to `.png` format with the specified compression level.
    3. Skips images that do not meet the criteria, logging the reasons.
    """
    os.makedirs(output_dir, exist_ok=True)  # Ensure the output directory exists.
    valid_images = []  # List to store paths of valid processed images.

    for input_file in input_files:
        try:
            with Image.open(input_file) as img:
                # Get image dimensions.
                width, height = img.size
                smaller_side = min(width, height)
                total_pixels = width * height

                # Check if the image meets the size criteria.
                if smaller_side >= min_side and total_pixels <= max_pixels:
                    # Generate the output file name.
                    output_file = os.path.join(output_dir, os.path.basename(input_file).replace(".tif", ".png"))
                    # Save the image as a PNG with specified compression.
                    img.save(output_file, format="PNG", compress_level=compression_level)
                    valid_images.append(output_file)  # Add the valid image to the list.
                    print(f"Converted and saved: {output_file}")
                else:
                    print(f"Skipped {input_file}: Dimensions {width}x{height} (does not meet criteria)")
        except Exception as e:
            print(f"Failed to process {input_file}: {e}")  # Log any errors during processing.

    return valid_images

def main():
    """
    Main function to parse arguments and orchestrate the image processing workflow.

    This function:
    1. Parses command-line arguments to specify input CSV, column, and other parameters.
    2. Downloads `.tif` images from URLs in the specified CSV column.
    3. Converts the downloaded `.tif` images to `.png` format.
    4. Filters the images based on specified size criteria.
    """
    parser = argparse.ArgumentParser(description="Download, convert, and filter images from a CSV file.")
    parser.add_argument("--csv_file", required=True, help="Path to the CSV file containing image URLs.")
    parser.add_argument("--column", required=True, help="Column name in the CSV file containing URLs.")
    parser.add_argument("--output_dir", required=True, help="Directory to save the processed images.")
    parser.add_argument("--compression", type=int, default=6, help="PNG compression level (0-9).")
    parser.add_argument("--min_side", type=int, default=512, help="Minimum size of the smaller side of the image.")
    parser.add_argument("--max_pixels", type=int, default=768**2, help="Maximum total number of pixels.")

    args = parser.parse_args()  # Parse the arguments from the command line.

    print("Downloading images...")
    tif_files = download_images(args.csv_file, args.column, args.output_dir)  # Step 1: Download images.

    print("Converting and filtering images...")
    convert_and_filter_images(
        tif_files,
        args.output_dir,
        compression_level=args.compression,
        min_side=args.min_side,
        max_pixels=args.max_pixels
    )  # Step 2: Convert and filter images.

if __name__ == "__main__":
    main()