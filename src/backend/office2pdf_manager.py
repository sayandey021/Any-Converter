import os
import requests
import zipfile
import io
import sys

def get_office2pdf_exe():
    """
    Returns the path to the office2pdf binary.
    If it does not exist, it downloads it from GitHub releases.
    """
    if sys.platform != "win32":
        return None # Currently we only handle Windows downloading in this wrapper

    # Determine paths
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    bin_dir = os.path.join(base_dir, 'bin', 'office2pdf')
    exe_path = os.path.join(bin_dir, 'office2pdf.exe')

    if os.path.exists(exe_path):
        return exe_path

    # Need to download
    os.makedirs(bin_dir, exist_ok=True)
    try:
        repo = 'developer0hye/office2pdf'
        url = f'https://api.github.com/repos/{repo}/releases/latest'
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        download_url = None
        for asset in data.get('assets', []):
            if 'windows-msvc' in asset['name'] and asset['name'].endswith('.zip'):
                download_url = asset['browser_download_url']
                break
                
        if not download_url:
            raise Exception("Could not find Windows binary in latest release.")
            
        print(f"Downloading office2pdf from {download_url}...")
        r_bin = requests.get(download_url, timeout=30)
        r_bin.raise_for_status()
        
        with zipfile.ZipFile(io.BytesIO(r_bin.content)) as z:
            z.extractall(bin_dir)
            
        # The zip might contain a nested folder. Let's find the .exe and move it.
        for root, dirs, files in os.walk(bin_dir):
            if 'office2pdf.exe' in files:
                found_exe = os.path.join(root, 'office2pdf.exe')
                if found_exe != exe_path:
                    import shutil
                    shutil.move(found_exe, exe_path)
                break
                
        if os.path.exists(exe_path):
            return exe_path
        else:
            raise Exception("office2pdf.exe not found after extraction.")
            
    except Exception as e:
        print(f"Failed to download office2pdf: {e}")
        return None
