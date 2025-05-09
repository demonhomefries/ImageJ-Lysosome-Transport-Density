import pandas as pd
import argparse
import os

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

def concat_dfs(filepaths):
    df_all = []
    for file in filepaths:
        df_all.append(pd.read_csv(file, low_memory=False))

    df_final = pd.concat(df_all, axis=0, ignore_index=True)
    df_final["wellID"] = df_final["Slice"].apply(lambda x: x.split("_")[1].split(".")[0])
    return df_final

def extract_well_id(tag: str):
    """
    Return the first 96‑ or 384‑well ID found in an underscore‑delimited string.
    Works even when the token is immediately followed by extra text (e.g. '.tif').
    """
    if not isinstance(tag, str):
        return None

    def is_well_token(tok: str):
        if len(tok) < 2:
            return False, None

        row = tok[0].upper()
        # grab the consecutive digits right after the row letter
        digits = ''
        for ch in tok[1:]:
            if ch.isdigit():
                digits += ch
            else:
                break  # stop at the first non‑digit ('.', '_', etc.)

        if not digits:
            return False, None

        col = int(digits.lstrip('0') or '0')  # allow leading zeros

        # 96‑well limits
        if "A" <= row <= "H" and 1 <= col <= 12:
            return True, f"{row}{col}"
        # 384‑well limits
        if "A" <= row <= "P" and 1 <= col <= 24:
            return True, f"{row}{col}"

        return False, None

    for chunk in tag.split("_"):
        ok, well = is_well_token(chunk)
        if ok:
            return well
    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script that merges CSV files generated for lysosome transport density calculations."
    )
    parser.add_argument("--outputPath", required=True, type=str, help="Output .csv filepath")
    parser.add_argument("--MIPfolder", required=True, type=str, help="Folder path for results from max intensity projection particle analysis CSVs")
    parser.add_argument("--T0folder", required=True, type=str, help="Folder path for results from T0 slice particle analysis CSVs")
    args = parser.parse_args()

    print("*****************lysosome_density_csv_merge_script.py STARTING*****************")
    # Grab the CSV list string and convert it back into a list of filepaths

    print("MIP folder:", args.MIPfolder)
    print("T0 folder:", args.T0folder)
    print("Output path:", args.outputPath)


    basedir = args.T0folder
    MIPFiles = find_files_surfacedir(args.MIPfolder, ".csv")
    T0Files = []
    for MIP_fp in MIPFiles:

        # Construct corresponding T0 file path
        T0_fp = os.path.join(basedir, os.path.basename(MIP_fp).replace("_mip_results.csv", "_t0_results.csv"))
        
        # Check if the corresponding T0 file exists
        if not os.path.isfile(T0_fp):
            print(f"ERROR: Could not find corresponding T0 file for {MIP_fp}")
            print(f"Looked for {T0_fp}")
            print(f"Make sure your files are named \"_mip_results.csv\", \"_t0_results.csv\"")
            print("Exiting program without merging CSVs.")
            exit()
        
        T0Files.append(T0_fp)


    mip_df = concat_dfs(MIPFiles)
    t0_df = concat_dfs(T0Files)
    
    # Old code: doesn't remove multiple instances of MAX_ or DUP_
    # # Build a helper that removes “MAX_” or “DUP_” (only at the start).
    # clean_slice = lambda s: s.str.replace(r'^(MAX|DUP)_', '', regex=True)
    # mip_df['slice_key'] = mip_df['Slice'].replace("MAX_", "").replace("DUP_", "")
    # t0_df['slice_key']  = t0_df['Slice'].replace("MAX_", "").replace("DUP_", "")

    # New code:
    # Add a temporary key column containing the cleaned filename
    mip_df['slice_key'] = (mip_df['Slice'].str.replace(r'(?:MAX_|DUP_)', '', regex=True))
    t0_df['slice_key'] = (t0_df['Slice'].str.replace(r'(?:MAX_|DUP_)', '', regex=True))

    # Merge the file based on the slice_key column (the image file name without the MAX or DUP prefix)
    final_df = pd.merge(mip_df, t0_df, on="slice_key", how="outer", indicator="merge_status")

    # Calculated column
    final_df["Transport Density"] = final_df["Total Area_y"] / final_df["Total Area_x"]
    final_df.drop(["wellID_x", "wellID_y"], axis=1, inplace=True)
    final_df["WellID"] = final_df["Slice_x"].apply(extract_well_id)
    final_df.to_csv(args.outputPath, index=False)
    print("Final CSV saved to:", args.outputPath)
    print("*****************lysosome_density_csv_merge_script.py COMPLETED*****************")
