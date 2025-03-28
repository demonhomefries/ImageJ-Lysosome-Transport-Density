# Change the settings dictionary below (line 3-8) according to your needs
# Drag this file into Fiji ImageJ and hit run


settings = {
    "tiff_input_dir" : r"T:\Users\images",
    "threshold_high": 20617,
    "threshold_low": 65535,
    "merge_script": r"\lysosome_density_csv_merge_script.py"
}
# settings["tiff_input_dir"] = r"C:\Users\auto_lyso_transport_density" # FOR TESTING ONLY





import os
import shutil
import json
import subprocess
from ij import IJ
from ij.plugin import ZProjector
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

"""
OUTPUT FILEPATHS:
input_dir/automated_lysosome transport analysis 
    /MIP (max intensity projection)
    /T0 (time point 0)
    /MIP Analyze particles Table
    /T0 Table
    /results.csv
"""


# Output image directories ("mip" = max intensity projection, "t0" = time point 0)

output_dir = os.path.join(settings["tiff_input_dir"], "automated_lysosome_transport_analysis")
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

    IJ.setAutoThreshold(imp, "Default dark no-reset")
    IJ.run(imp, "Convert to Mask", "background=Dark calculate black")

    # Save the T0 image
    t0 = imp.crop("1-1")
    print("\tSliced imp to t0")
    IJ.save(t0, t0_tif_fp)
    print("\tSaved t0")
    IJ.run(t0, "Analyze Particles...", "summarize")
    print("\tt0 analyzed")
    IJ.saveAs("Results", t0_tables_output_fp)
    print("\tt0 results saved")
    t0.close()

    mip = ZProjector.run(imp,"max")
    print("\n\tCreated MIP")
    IJ.save(mip, mip_tif_fp)
    print("\tSaved MIP")
    IJ.run(mip, "Analyze Particles...", "summarize")
    print("\tMIP analyzed")
    IJ.saveAs("Results", mip_tables_output_fp)
    print("\tMIP results saved")
    mip.close()

    imp.close()

    print("Finished: {}".format(tif_name))


command = "python " + settings["merge_script"] + " --outputPath " + settings["merged_csv_output_fp"] + " --MIPfolder \"" + mip_tables_output_dir + "\" --T0folder \"" + t0_tables_output_dir + "\""
print(command)

output_message = subprocess.check_output(command)
print(output_message)
print("Completed Successfully")