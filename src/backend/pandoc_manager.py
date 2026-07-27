import os
import zipfile
import urllib.request
import tempfile
import stat

PANDOC_URL = "https://github.com/jgm/pandoc/releases/download/3.10.1/pandoc-3.10.1-windows-x86_64.zip"

def get_pandoc_exe():
    """
    Returns the path to the pandoc executable.
    If it doesn't exist, downloads and extracts it into the bin/ folder.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    bin_dir = os.path.join(base_dir, "bin")
    
    if os.name == 'nt':
        exe_path = os.path.join(bin_dir, "pandoc.exe")
    else:
        # For simplicity, assuming windows as per original requirements,
        # but could support mac/linux similarly.
        exe_path = os.path.join(bin_dir, "pandoc")
        
    if os.path.exists(exe_path):
        return exe_path
        
    os.makedirs(bin_dir, exist_ok=True)
    
    print("Downloading pandoc (this may take a moment)...")
    
    try:
        # Download the zip file
        temp_zip = tempfile.mktemp(suffix=".zip")
        urllib.request.urlretrieve(PANDOC_URL, temp_zip)
        
        # Extract the exe
        with zipfile.ZipFile(temp_zip, 'r') as zf:
            for file_info in zf.infolist():
                if file_info.filename.endswith("pandoc.exe"):
                    # Extract to a temp dir then move to bin
                    temp_extract = tempfile.mkdtemp()
                    zf.extract(file_info, temp_extract)
                    
                    extracted_exe = os.path.join(temp_extract, file_info.filename)
                    with open(extracted_exe, 'rb') as f_in:
                        with open(exe_path, 'wb') as f_out:
                            f_out.write(f_in.read())
                    break
        
        if os.path.exists(temp_zip):
            os.remove(temp_zip)
            
        if not os.path.exists(exe_path):
            raise Exception("pandoc.exe not found in downloaded archive.")
            
        # Ensure executable permissions
        st = os.stat(exe_path)
        os.chmod(exe_path, st.st_mode | stat.S_IEXEC)
        
        return exe_path
        
    except Exception as e:
        print(f"Failed to download/extract pandoc: {e}")
        return None
