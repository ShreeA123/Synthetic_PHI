import os
import pandas as pd
from faker import Faker
import hashlib
from PIL import Image, ImageDraw, UnidentifiedImageError
import numpy as np

def generate_patient_identity(file_path):
    # Create a deterministic seed based on the image's file path.
    # This ensures that if you re-run the script, the exact same image gets the exact same fake data.
    seed = int(hashlib.md5(file_path.encode('utf-8')).hexdigest(), 16) % (10**8)
    Faker.seed(seed)
    fake = Faker()
    
    # Return a dictionary containing the synthetic patient information to be used as PHI.
    return {
        "PatientName": fake.name(),
        "PatientID": fake.uuid4()[:8],
        "PatientBirthDate": fake.date_of_birth(minimum_age=18, maximum_age=90).strftime("%Y%m%d"),
        "StudyDate": fake.date_between(start_date="-2y", end_date="today").strftime("%Y%m%d"),
        "AccessionNumber": fake.bban()
    }

def burn_phi_to_image(image_path, patient_data, output_path):
    try:
        # Open the original ultrasound image and convert it to RGB mode for text rendering.
        img = Image.open(image_path).convert("RGB")
    except (UnidentifiedImageError, OSError) as e:
        # If the file is corrupted, empty, or unreadable, print a warning and skip it.
        print(f"⚠️ Skipping unreadable file: {os.path.basename(image_path)}")
        return None

    draw = ImageDraw.Draw(img)
    
    # SAFETY CHECK: Evaluate the top-left corner of the image.
    crop_region = img.crop((0, 0, 300, 50))
    if np.mean(crop_region) > 50: 
        return None
        
    # Format the synthetic PHI text that will be burned into the image pixels.
    phi_text = f"Name: {patient_data['PatientName']}\nID: {patient_data['PatientID']}\nDOB: {patient_data['PatientBirthDate']}"
    
    # Set the coordinates (x, y) where the text will start.
    text_position = (10, 10)
    
    # Draw the white text onto the image and save it to the output folder.
    draw.text(text_position, phi_text, fill="white")
    img.save(output_path)
    
    # Calculate and return the exact bounding box coordinates of the text.
    bbox = draw.textbbox(text_position, phi_text)
    return {"text": phi_text, "bounding_box": bbox}

def get_all_images_from_patient(patient_path):
    """
    NEW FUNCTION: Scans a patient's directory and returns a list of all image paths, 
    whether they are directly inside the folder or hidden inside nested batch folders.
    """
    image_paths = []
    
    # Condition 1: Check for images sitting directly in the main patient folder
    for item in os.listdir(patient_path):
        if item.lower().endswith((".jpg", ".png", ".jpeg")):
            image_paths.append(os.path.join(patient_path, item))
            
    # Condition 2: Check for images nested inside 'processed_' batch folders
    batch_folders = [f for f in os.listdir(patient_path) if f.startswith("processed_") and os.path.isdir(os.path.join(patient_path, f))]
    for batch_folder in batch_folders:
        images_dir = os.path.join(patient_path, batch_folder, "images")
        
        # If the nested 'images' directory exists, grab all images inside it
        if os.path.exists(images_dir):
            for img_name in os.listdir(images_dir):
                if img_name.lower().endswith((".jpg", ".png", ".jpeg")):
                    image_paths.append(os.path.join(images_dir, img_name))
                    
    return image_paths

def main():
    
    # 1. Base path updated to your new location containing the dataset.
    base_path = r"C:\Users\shree\Downloads\Database\Lung Database"
    
    # 2. Output directory where the new synthetic images will be saved.
    output_base_dir = r"D:\Work\Synthetic_PHI_Dataset"
    
    # Automatically create the output directory if it doesn't already exist.
    os.makedirs(output_base_dir, exist_ok=True)

    # Initialize an empty list to store the ground-truth data (text and bounding boxes).
    ground_truth_records = []

    # Iterate through every patient folder (e.g., 'Pt93.21') in your base dataset directory.
    for patient_folder in os.listdir(base_path):
        patient_path = os.path.join(base_path, patient_folder)
        
        # Skip any files that aren't directories (such as hidden .DS_Store system files).
        if not os.path.isdir(patient_path):
            continue
            
        # Use our new function to find all images, regardless of the folder structure
        image_paths = get_all_images_from_patient(patient_path)
        
        # Process each individual image file found
        for img_path in image_paths:
            img_name = os.path.basename(img_path)
            
            # Create a unique filename for the output image combining the patient folder and original image name.
            output_img_path = os.path.join(output_base_dir, f"{patient_folder}_{img_name}")
            
            # Step 1: Generate the synthetic patient identity.
            patient_data = generate_patient_identity(img_path)
            
            # Step 2: Burn the synthetic PHI into the image pixels.
            result = burn_phi_to_image(img_path, patient_data, output_img_path)
            
            # Step 3: If the image passed the safety check and was processed, record its ground truth.
            if result:
                ground_truth_records.append({
                    "original_file": img_path,
                    "synthetic_file": output_img_path,
                    "patient_id": patient_data["PatientID"],
                    "patient_name": patient_data["PatientName"],
                    "burned_text": result["text"],
                    "bounding_box": result["bounding_box"] # Used for later evaluation of de-identification models.
                })

    # Convert the collected ground-truth records into a pandas DataFrame.
    ground_truth_df = pd.DataFrame(ground_truth_records)
    
    # Export the DataFrame as a CSV file to act as the answer key for your future pipeline.
    ground_truth_df.to_csv(os.path.join(output_base_dir, "master_phi_ground_truth.csv"), index=False)
    print("Dataset generation complete. Ground truth saved.")

if __name__ == "__main__":
    main()
