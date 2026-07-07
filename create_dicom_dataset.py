import os
import pandas as pd
import numpy as np
import pydicom
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import generate_uid
import datetime
from PIL import Image
import re

def convert_to_dicom():
    # --- UPDATE THIS TO YOUR ACTUAL CSV LOCATION ---
    csv_path = r"D:\Work\Synt_data_gen\sample_data\master_phi_ground_truth.csv"
    
    if not os.path.exists(csv_path):
        print(f"Error: Could not find CSV at {csv_path}")
        return

    print("Reading Ground Truth CSV...")
    df = pd.read_csv(csv_path)
    
    for index, row in df.iterrows():
        image_path = str(row['synthetic_file'])
        
        if not os.path.exists(image_path):
            print(f"⚠️ Image not found, skipping: {image_path}")
            continue
            
        # Define the output path for the new DICOM file
        output_dcm_path = image_path.replace('.jpg', '.dcm').replace('.png', '.dcm')

        # 1. Read the modified image pixels
        img = Image.open(image_path).convert('RGB')
        np_frame = np.array(img)

        # 2. Create the DICOM File Meta Information
        file_meta = FileMetaDataset()
        file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.6.1' # Ultrasound Image Storage
        file_meta.MediaStorageSOPInstanceUID = generate_uid()
        file_meta.TransferSyntaxUID = '1.2.840.10008.1.2.1' # Explicit VR Little Endian

        # 3. Initialize the DICOM Dataset
        ds = FileDataset(output_dcm_path, {}, file_meta=file_meta, preamble=b"\0" * 128)

        # 4. Inject the Synthetic PHI from the CSV into the headers
        ds.PatientName = str(row['patient_name'])
        ds.PatientID = str(row['patient_id'])

        # --- THE NEW ROUTE: ROBUST REGEX EXTRACTION ---
        # This searches the burned_text specifically for "DOB:" followed by numbers
        burned_text = str(row['burned_text'])
        dob_match = re.search(r'DOB:\s*(\d+)', burned_text)
        
        # If it finds the date, it uses it. If not, it safely defaults to 19000101.
        ds.PatientBirthDate = dob_match.group(1) if dob_match else "19000101"

        # Add Study Date
        ds.StudyDate = datetime.datetime.now().strftime('%Y%m%d')
        ds.AccessionNumber = "SYNTH-" + str(row['patient_id'])

        # 5. Enforce DICOM realism standards
        ds.Modality = 'US'
        ds.StudyInstanceUID = generate_uid()
        ds.SeriesInstanceUID = generate_uid()
        ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
        ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
        
        # Tagging as DERIVED/SECONDARY ensures it is not mistaken for a primary clinical scan
        ds.ImageType = ['DERIVED', 'SECONDARY']
        ds.Manufacturer = 'SYNTHETIC-DEID-PIPELINE'

        # 6. Embed the Pixel Data
        ds.SamplesPerPixel = 3
        ds.PhotometricInterpretation = "RGB"
        ds.PlanarConfiguration = 0
        ds.Rows = np_frame.shape
        ds.Columns = np_frame.shape[3]
        ds.BitsAllocated = 8
        ds.BitsStored = 8
        ds.HighBit = 7
        ds.PixelRepresentation = 0
        ds.PixelData = np_frame.tobytes()

        # Set endianness
        ds.is_little_endian = True
        ds.is_implicit_VR = False

        # 7. Save the final DICOM file
        ds.save_as(output_dcm_path)
        print(f"✅ Packaged DICOM: {os.path.basename(output_dcm_path)}")

if __name__ == "__main__":
    convert_to_dicom()
    print("\n🎉 DICOM Packaging Complete!")