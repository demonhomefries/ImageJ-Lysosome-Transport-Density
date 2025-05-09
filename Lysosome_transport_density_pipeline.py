# Change the settings dictionary below (line 6-14) according to your needs
# Drag this file into Fiji ImageJ and hit run


settings = {
    "tiff_input_dir" : r"C:\Users\akmishra\Desktop\LTDTest",
    "threshold_high": 20617,
    "threshold_low": 65535,
    "merge_script": r"C:\Users\akmishra\Desktop\ImageJ-Lysosome-Transport-Density\lysosome_density_csv_merge_script.py",
    "crop": True,
    "crop_x": 543,
    "crop_y": 0,
    "crop_width": 1417,
    "crop_height": 1960
}



import os
import shutil
import json
import subprocess
from datetime import date
from ij import IJ
from ij.gui import Roi
from ij.plugin import ZProjector, Duplicator
from ij.measure import ResultsTable
from ij.plugin.filter import ParticleAnalyzer
from java.lang import Double

def find_files_surfacedir(directory, extension=".tif"):
    files = []
    for item in os.listdir(directory):
        # Construct full file path
        full_path = os.path.join(directory, item)
        # Check if it's a file and has the specified extension
        if item.endswith(extension):
            #print(f"Adding {full_path} to list!")
            files.append(full_path)

    return files

def ensure_quoted(path: str):
    """
    Probably the stupidest function ever, but somehow neccesary
    """
    # Just return it normally if it's already quoted
    if len(path) >= 2 and path[0] == path[-1] and path[0] in {"'", '"'}:
        return path
    # Wrap it in double quotes if not
    return f'"{path}"'

"""
OUTPUT FILEPATHS:
input_dir/{today}_automated_lysosome transport analysis 
    /MIP (max intensity projection)
    /T0 (time point 0)
    /MIP Analyze particles Table
    /T0 Table
    /results.csv
"""


# Output image directories ("mip" = max intensity projection, "t0" = time point 0)
today = date.today().strftime("%Y_%m_%d")
output_dir = os.path.join(settings["tiff_input_dir"], today + "_automated_lysosome_transport_analysis")
mip_tif_output_dir = os.path.join(output_dir, "auto_mip_tifs")
t0_tif_output_dir = os.path.join(output_dir, "auto_t0_tifs")

# Output table directories
mip_tables_output_dir = os.path.join(output_dir, "auto_mip_results_tables")
t0_tables_output_dir = os.path.join(output_dir, "auto_t0_results_tables")

# Output CSV file
results_csv_output_fp = os.path.join(output_dir, "auto_final_results.csv")
settings["merged_csv_output_fp"] = results_csv_output_fp

# Generate Directory Tree:
for directory in [output_dir, mip_tif_output_dir, t0_tif_output_dir, mip_tables_output_dir, t0_tables_output_dir]:
    if not os.path.exists(directory):
        os.makedirs(directory)


tif_file_list = find_files_surfacedir(settings["tiff_input_dir"])

for tif_fp in tif_file_list:

    # Create the output filenames
    tif_name = os.path.basename(tif_fp).split(".")[0]
    # Images:
    t0_tif_fp = os.path.join(t0_tif_output_dir, "{}_auto_t0.tif".format(tif_name))
    mip_tif_fp = os.path.join(mip_tif_output_dir, "{}_auto_mip.tif".format(tif_name))
    # Tables:
    mip_tables_output_fp = os.path.join(mip_tables_output_dir, "{}_auto_mip_results.csv".format(tif_name))
    t0_tables_output_fp = os.path.join(t0_tables_output_dir, "{}_auto_t0_results.csv".format(tif_name))

    print("Starting Process for: {}".format(tif_name))


    # Open the image
    imp = IJ.openImage(tif_fp)
    
    # Check dimensions
    w = imp.getWidth()
    h = imp.getHeight()
    z = imp.getNSlices()
    c = imp.getNChannels()
    t = imp.getNFrames()

    print("Size: {} × {} px,  Z‑slices={},  channels={},  frames={}".format(w, h, z, c, t))


    IJ.setAutoThreshold(imp, "Default dark no-reset")
    IJ.run(imp, "Convert to Mask", "background=Dark calculate black")

    crop_x = settings["crop_x"]
    crop_y = settings["crop_y"]
    crop_w = settings["crop_width"]
    crop_h = settings["crop_height"]

    # Save the T0 image
    t0 = imp.crop("1-1")
    print("\tSliced imp to t0")
    if settings["crop"] == True:
        print("\tPerforming crop on t0")
        t0.setRoi(Roi(crop_x, crop_y, crop_w, crop_h))
        t0 = Duplicator().run(t0, 1, 1)
    IJ.save(t0, t0_tif_fp)
    print("\tSaved t0")
    IJ.run(t0, "Analyze Particles...", "summarize")
    print("\tt0 analyzed")
    IJ.saveAs("Results", t0_tables_output_fp)
    print("\tt0 results saved")

    # check dimensions
    w = t0.getWidth()
    h = t0.getHeight()
    z = t0.getNSlices()
    c = t0.getNChannels()
    t = t0.getNFrames()
    print("\tt0 Size: {} × {} px,  Z‑slices={},  channels={},  frames={}".format(w, h, z, c, t))

    t0.close()

    mip = ZProjector.run(imp,"max")
    print("\n\tCreated MIP")
    if settings["crop"] == True:
        print("\tPerforming crop on t0")
        mip.setRoi(Roi(crop_x, crop_y, crop_w, crop_h))
        mip = Duplicator().run(mip, 1, 1)
    IJ.save(mip, mip_tif_fp)
    print("\tSaved MIP")
    IJ.run(mip, "Analyze Particles...", "summarize")
    print("\tMIP analyzed")
    IJ.saveAs("Results", mip_tables_output_fp)
    print("\tMIP results saved")

    # check dimensions
    w = mip.getWidth()
    h = mip.getHeight()
    z = mip.getNSlices()
    c = mip.getNChannels()
    t = mip.getNFrames()
    print("\tmip Size: {} × {} px,  Z‑slices={},  channels={},  frames={}".format(w, h, z, c, t))

    mip.close()

    imp.close()

    print("Finished: {}".format(tif_name))


command = "python " + ensure_quoted(settings["merge_script"]) + " --outputPath " + ensure_quoted(settings["merged_csv_output_fp"]) + " --MIPfolder " + ensure_quoted(mip_tables_output_dir) + " --T0folder " + ensure_quoted(t0_tables_output_dir) + ""
print(command)

output_message = subprocess.check_output(command)
print(output_message)
print("Completed Successfully")