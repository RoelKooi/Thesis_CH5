# -*- coding: utf-8 -*-
"""
Created on Wed Jan 15 14:13:25 2025

@author: 20201634
"""

import os
import cv2
import numpy as np
import matplotlib.pyplot as plt

def main():
    folder = r"D:\A2F4_MCF10a\Cilia_Ctrl\Masks\Eroded"
    combine_series(folder)
        
def merge_images(folder, prog=0, total=0):
    """All images in folder must be of same dimensions"""
    result = None
    print("Merging images in folder '{}'".format(folder))
    for f in os.listdir(folder):
        if f.split('.')[-1] in ('png', 'jpg', 'tif', 'tiff'): # Check if the file type is an image file type
            prog += 1
            print("Image {} of {}".format(prog, total))
            if result is None:
                result = cv2.imread("/".join((folder, f)))
            else:
                result = result + cv2.imread("/".join((folder, f)))
    return result, prog

def combine_series(folder, output_ext="tiff"):
    """Folder should contain only folders with images to be combined.
    The structure is such that each of the subfolders' names will be the name of the combined resulting images.
    The list of combined images will be save in a new created subfolder of 'folder' called ~/Combined
    """
    # Assess the total amount of images
    count = 0
    for sub in os.listdir(folder):
        subfolder = "/".join((folder, sub))
        if os.path.isdir(subfolder):
            count += len(os.listdir(subfolder))
    
    print("Total of {} images found".format(count))
    progress_count = 0
    
    out_dir = folder + "/Combined"
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    
    for sub in os.listdir(folder):
        subfolder = "/".join((folder, sub))
        if os.path.isdir(subfolder) and not "Combined" in sub:
            r, p = merge_images(subfolder, prog=progress_count, total=count)
            if r is not None:
                progress_count = p
                print("Saving combined image '{}'".format(sub))
                cv2.imwrite(".".join(("/".join((out_dir, sub)), output_ext)), r)
            
    

if __name__ == "__main__":
    main()
