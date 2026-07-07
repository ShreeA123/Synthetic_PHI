import os
import pandas as pd
import numpy as np
import pydicom
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import generate_uid
import datetime
from PIL import Image

def generate_sample_data():
    """
    Generates a sample Ground Truth CSV and a dummy synthetic JPG image
    """
    os.makedirs("sample_data", exist_ok=True)
    
    # Create a dummy ultrasound-like image
    img = Image.new('RGB', (512, 512), color=(73, 109, 137))
    dummy_img_path = 'sample_data/synthetic_image.jpg'
    img.save(dummy_img_path)

    # Create a mock master_phi_ground_truth.csv matching our Project 1 format
    data = [{
        "original_file": "original_image.jpg",
        "synthetic_file": dummy_img_path,
        "patient_id": "8a7b6c5d",
        "patient_name": "Jane Synthetic",
        "burned_text": "Name: Jane Synthetic\nID: 8a7b6c5d\nDOB: 19851020",
        "study_date": "20231025",
        "bounding_box": "(10, 10, 200, 50)"
    }]
    
    csv_path = "sample_data/master_phi_ground_truth.csv"
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    print(f"✅ Generated sample CSV: {csv_path}")
    return csv_path

def convert_images_to_dicom(csv_path):
    """
    Reads the ground truth CSV, opens the modified JPGs, and packages them 
    into fully compliant DICOM files with synthetic PHI injected into the metadata.
    """
    df = pd.read_csv(csv_path)
    
    for index, row in df.iterrows():
        image_path = row['synthetic_file']
        
        # Define the output path for the new DICOM file
        output_dcm_path = image_path.replace('.jpg', '.dcm').replace('.png', '.dcm')

        # 1. Read the modified image pixels
        img = Image.open(image_path).convert('RGB')
        np_frame = np.array(img)

        # 2. Create the DICOM File Meta Information
        file_meta = FileMetaDataset()
        # UID for Ultrasound Image Storage
        file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.6.1' 
        file_meta.MediaStorageSOPInstanceUID = generate_uid()
        # Explicit VR Little Endian
        file_meta.TransferSyntaxUID = '1.2.840.10008.1.2.1' 

        # 3. Initialize the DICOM Dataset
        ds = FileDataset(output_dcm_path, {}, file_meta=file_meta, preamble=b"\0" * 128)

        # 4. Inject the Synthetic PHI from the CSV into the headers
        ds.PatientName = str(row['patient_name'])
        ds.PatientID = str(row['patient_id'])

        # Parse PatientBirthDate from the 'burned_text' column
        burned_text = str(row['burned_text'])
        dob = "19000101" # Safe default
        for line in burned_text.split('\n'):
            if line.startswith('DOB:'):
                # CORRECTED: Use index [2] to grab the date
                dob = line.split(':')[2].strip()
        ds.PatientBirthDate = dob

        # Add Study Date and Accession Number
        ds.StudyDate = str(row.get('study_date', datetime.datetime.now().strftime('%Y%m%d')))
        ds.AccessionNumber = "SYNTH-" + str(row['patient_id'])

        # 5. Enforce DICOM realism standards for synthetic data
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
        ds.Columns = np_frame.shape
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
        print(f"✅ Packaged fully compliant DICOM: {output_dcm_path}")

if __name__ == "__main__":
    # Step A: Generate the sample CSV and image
    sample_csv = generate_sample_data()
    
    # Step B: Read the CSV and create the DICOM file
    convert_images_to_dicom(sample_csv)
    print("\n🎉 Pipeline Complete!")