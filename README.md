Synthetic PHI Generation Pipeline
Project Description
This project focuses on building a Synthetic Protected Health Information (PHI) generation pipeline designed to safely evaluate and train medical image de-identification systems. Medical images inherently suffer from the "iceberg problem," where sensitive identifiers are not only visible as burned-in text on the image pixels but are also hidden within the structural metadata (like DICOM headers)
. Because real patient data is heavily restricted by privacy laws like HIPAA
, sharing or testing models on authentic data is legally challenging
.
This pipeline solves this by taking clean, open-source ultrasound images and injecting them with highly realistic, deterministically generated synthetic patient identities
. By generating the PHI ourselves, we achieve a perfect "ground truth"—knowing exactly what text was generated, its exact bounding box coordinates on the image, and the associated pseudonymized mapping IDs. This creates a robust foundation for benchmarking optical character recognition (OCR) and redaction models in future projects.
Dataset Overview
Dataset: Stanford Lung Database (OpenPOCUS)
.
Source: A multi-center prospective cohort study collecting lung point-of-care ultrasound (POCUS) views from adult patients presenting to emergency departments
.
Scope: 226 adult patients, perfectly balanced with 50% diagnosed with COVID-19 pneumonia and the rest comprising bacterial pneumonia, viral pneumonia, healthy controls, and other conditions
.
Data Features
Total Videos: 1,871 lung ultrasound video clips
.
Total Images: 324,027 individual frames, extracted and standardized to 512×512 pixels using letterboxing
.
Devices Used: Images were acquired using a mix of cart-based and handheld ultrasound devices (including Butterfly IQ, Vave, Sonosite, Echonous, and GE Venue)
.
Clinical Findings: The dataset contains diverse clinical features, including normal scans, B-lines, and subpleural/lobar consolidations
.
Data Set Location Format
The downloaded Stanford Lung Database follows a nested directory structure that must be parsed:
Root Directory: Contains ~226 individual patient folders (e.g., Pt93.21, Pt94.1).
Batch Zips: Inside patient folders, images are frequently compressed into archives named with the prefix processed_<number>_images_batch.zip.
Direct Images: Some patient folders do not contain nested batches and instead house .jpg or .png ultrasound frames directly in the root of the patient folder.
Metadata: Each batch contains a meta data.csv mapping the images to their clinical labels.
Key Files
unzip_batches.py: A utility script to parse the complex directory structure and extract the nested image batches.
synthetic_phi.py: Generates deterministic fake patient identities, safely burns the text onto the dark borders of the ultrasound frames, and exports a master ground-truth CSV.
create_dicom_dataset.py: (NEW) Reads the ground truth CSV, converts the modified .jpg/.png frames into .dcm files, and uses robust Regular Expressions (Regex) to safely inject the synthetic identity directly into the DICOM metadata headers
.
Project Workflow
1. Data Extraction (unzip_batches.py) A utility script traverses the root directory to locate and automatically extract all processed_<number>_images_batch.zip files directly into their respective patient folders while leaving system files (like .DS_Store) untouched.
2. Synthetic Identity Generation The synthetic_phi.py pipeline iterates through every extracted image. It utilizes the Python Faker library, seeded by the unique hash of the image file path, to create deterministic fake patient profiles (Names, DOBs, synthetic MRNs). This ensures absolute reproducibility across pipeline runs.
3. Pixel Burn-In and Safety Checking (Visual PHI) Before applying the synthetic text, the pipeline evaluates the pixel brightness of the top-left region of the ultrasound frame. If the region is sufficiently dark, it renders the white PHI text onto the image to simulate burned-in ultrasound identifiers. If the region is too bright (indicating the ultrasound fan might be obscured), the image is safely skipped.
4. Ground Truth Compilation For every successfully modified image, the pipeline calculates the bounding box coordinates of the injected text. This data is exported to a master_phi_ground_truth.csv file, providing a structured answer key mapping the original file, the synthetic file, the injected text, and the bounding box for downstream evaluation.
5. DICOM Packaging and Metadata Injection (Hidden PHI) (NEW) To complete the simulation of the "Iceberg Problem", the create_dicom_dataset.py script reads the ground-truth CSV and wraps the modified images into a fully compliant Digital Imaging and Communications in Medicine (DICOM) format (.dcm)
. It then injects the exact same synthetic PHI (e.g., (0010,0010) Patient's Name and (0010,0020) Patient ID) into the DICOM headers
. It utilizes robust Regex to parse specific data points like Date of Birth safely.
Project Insights
Solving the Iceberg Problem: By simulating both visual PHI (pixels) and hidden PHI (metadata), this pipeline accurately reflects the complex realities of healthcare data
.
Perfect Validation: Because the pipeline generated the data, you can objectively score downstream de-identification models. If a redaction tool misses a name, or blurs the wrong coordinates, your ground-truth CSV will instantly flag the failure.
Overcoming Privacy Bottlenecks: Synthetic datasets allow data science teams to rapidly prototype, share, and benchmark healthcare AI tools without waiting for lengthy institutional review board (IRB) approvals or risking HIPAA violations
.
Tech Stack
Language: Python 3
Data Processing: Pandas, NumPy, Regular Expressions (re)
Image Manipulation: Pillow (PIL)
Medical Formats: pydicom
Synthetic Data: Faker
Environment: VS Code
Installation and Setup
1. Environment Creation Create and activate a virtual environment to keep dependencies isolated:
# Windows
python -m venv deid_env
deid_env\Scripts\activate

# Mac/Linux
python3 -m venv deid_env
source deid_env/bin/activate
2. Install Dependencies Install the required packages for image processing, medical formats, and synthetic data generation:
pip install pandas numpy pillow faker pydicom
Project Cloning Procedure
To set up this project locally on your machine, follow these steps:
1. Clone the Repository Open your VS Code terminal and run the following git command to clone the project:
git clone https://github.com/yourusername/Synthetic-PHI-Pipeline.git
cd Synthetic-PHI-Pipeline
2. Download the Dataset Download the Stanford Lung Database (OpenPOCUS) and place the extracted parent folder into your local Downloads or Data directory.
3. Configure File Paths Open the pipeline scripts in VS Code:
In unzip_batches.py, update the ROOT variable to point to your Stanford Lung Database folder.
In synthetic_phi.py, update base_path to match your dataset directory and output_base_dir to the folder where you want your new images saved.
In create_dicom_dataset.py, update csv_path to point to the master_phi_ground_truth.csv file generated by the previous step.
4. Execute the Pipeline Run the extraction utility first, followed by the image generation pipeline, and finally the DICOM packaging:
python unzip_batches.py
python synthetic_phi.py
python create_dicom_dataset.py
Check your output directory for the newly generated .dcm files with injected visual and metadata PHI alongside the master ground truth CSV!
Troubleshooting & Common Errors
If you encounter issues while running the pipeline, refer to the following common errors and their solutions:
1. ModuleNotFoundError: No module named 'pandas'
Cause: Your virtual environment was deactivated. When this happens, VS Code defaults to your computer's global Python installation, which does not have the project-specific libraries installed.
Solution: Reactivate your virtual environment inside your VS Code terminal (e.g., run .\.venv\Scripts\activate). You will know it is successful when (.venv) appears at the start of your command prompt. Once activated, simply run your script again.
2. Unreadable Image Error (PIL.UnidentifiedImageError)
Cause: When processing large, crowdsourced medical datasets, it is common to encounter occasional 0-byte, system-generated, or corrupted files mixed in with valid .jpg or .png images. The Pillow (PIL) library crashes when it attempts to open these invalid files.
Solution: The script handles this gracefully by using a try...except block targeting UnidentifiedImageError and OSError. Instead of halting the entire pipeline, the script will output a warning (⚠️ Skipping unreadable file...) and safely proceed to process the next valid image.
3. KeyboardInterrupt Error
Cause: The script was manually interrupted or paused mid-execution. This usually happens if you press Ctrl + C in the terminal, or if you accidentally click and highlight text inside the terminal window (which pauses the process in some environments).
Solution: Evaluating pixel brightness and rendering text for hundreds of thousands of images is a computationally intensive task. Run the script again and allow it to process continuously without terminal interaction until it explicitly prints completion.
4. IndexError: list index out of range (During DICOM Creation)
Cause: Occurs when using basic string .split(':') to parse text like "DOB: 19851020". If the formatting varies even slightly, Python creates a list that does not contain the expected number of items, causing the index request to fail and crash the pipeline.
Solution: The pipeline was upgraded to use robust Regular Expressions (re.search(r'DOB:\s*(\d+)', burned_text)). This acts as a search engine that directly scans for the numbers following "DOB:", completely avoiding fragile string splitting and indexing errors.
5. UserWarning / IndexError: tuple index out of range (During DICOM Creation)
Cause: The pydicom library expects strict integers for DICOM dimensions like Rows and Columns. Attempting to assign np_frame.shape directly passes a 3D tuple (height, width, color channels), which causes a UserWarning. Attempting to fix it by using a non-existent index (like 
) causes a tuple IndexError.
Solution: Explicitly assign the exact integer dimensions from the tuple: ds.Rows = np_frame.shape (height) and ds.Columns = np_frame.shape
 (width).
