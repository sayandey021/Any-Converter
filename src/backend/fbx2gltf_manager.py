import os
import requests
import sys

def get_fbx2gltf_exe():
    """
    Returns the path to the FBX2glTF binary.
    If it does not exist, it downloads it from GitHub releases.
    """
    if sys.platform != "win32":
        return None # Currently we only handle Windows downloading in this wrapper

    # Determine paths
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    bin_dir = os.path.join(base_dir, 'bin', 'fbx2gltf')
    exe_path = os.path.join(bin_dir, 'FBX2glTF.exe')

    if os.path.exists(exe_path):
        return exe_path

    # Need to download
    os.makedirs(bin_dir, exist_ok=True)
    try:
        download_url = 'https://github.com/facebookincubator/FBX2glTF/releases/download/v0.9.7/FBX2glTF-windows-x64.exe'
            
        print(f"Downloading FBX2glTF from {download_url}...")
        r_bin = requests.get(download_url, timeout=60, stream=True)
        r_bin.raise_for_status()
        
        with open(exe_path, 'wb') as f:
            for chunk in r_bin.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                
        if os.path.exists(exe_path):
            return exe_path
        else:
            raise Exception("FBX2glTF.exe not found after download.")
            
    except Exception as e:
        print(f"Failed to download FBX2glTF: {e}")
        return None
