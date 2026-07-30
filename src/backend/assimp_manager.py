import os
import requests
import zipfile
import io
import sys
import ctypes

def get_assimp_dll():
    """
    Returns the path to the Assimp DLL.
    If it does not exist, it downloads it from GitHub releases.
    """
    if sys.platform != "win32":
        return None # Currently we only handle Windows downloading in this wrapper

    # Determine paths
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    bin_dir = os.path.join(base_dir, 'bin', 'assimp')
    dll_path = os.path.join(bin_dir, 'assimp.dll')

    if os.path.exists(dll_path):
        return dll_path

    # Need to download
    os.makedirs(bin_dir, exist_ok=True)
    try:
        download_url = 'https://github.com/assimp/assimp/releases/download/v6.0.5/windows-x64-v6.0.5.zip'
            
        print(f"Downloading Assimp from {download_url}...")
        r = requests.get(download_url, timeout=60, stream=True)
        r.raise_for_status()
        
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            # Find the dll in the zip
            for name in z.namelist():
                if name.endswith('.dll') and 'mt.dll' in name:
                    with z.open(name) as source, open(dll_path, "wb") as target:
                        target.write(source.read())
                    break
                
        if os.path.exists(dll_path):
            return dll_path
        else:
            raise Exception("Assimp DLL not found in the downloaded archive.")
            
    except Exception as e:
        print(f"Failed to download Assimp: {e}")
        return None

def get_assimp_export_id(ext):
    """
    Maps standard file extensions to Assimp format IDs.
    Returns the ID as bytes, or None if unsupported by Assimp export.
    """
    ext = ext.lower().replace('.', '')
    mapping = {
        'dae': b'collada',
        'x': b'x',
        'stp': b'stp',
        'obj': b'obj',
        'stl': b'stl',
        'ply': b'ply',
        '3ds': b'3ds',
        'gltf': b'gltf2',
        'glb': b'glb2',
        'fbx': b'fbx',
        'assbin': b'assbin',
        'assxml': b'assxml',
        'json': b'json'
    }
    return mapping.get(ext)

def convert_with_assimp(input_path, output_path, export_format_id=b"obj"):
    """
    Uses ctypes to natively invoke the Assimp C-API to convert a 3D model.
    """
    dll_path = get_assimp_dll()
    if not dll_path:
        raise Exception("Assimp DLL binary not found or could not be downloaded.")
    
    # Load Library
    try:
        dll = ctypes.cdll.LoadLibrary(dll_path)
    except Exception as e:
        raise Exception(f"Failed to load Assimp DLL: {e}")
        
    # Bind C-API methods
    dll.aiImportFile.restype = ctypes.c_void_p
    dll.aiImportFile.argtypes = [ctypes.c_char_p, ctypes.c_uint]

    dll.aiExportScene.restype = ctypes.c_int
    dll.aiExportScene.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]

    dll.aiReleaseImport.restype = None
    dll.aiReleaseImport.argtypes = [ctypes.c_void_p]
    
    # aiProcess_Triangulate = 0x8
    scene = dll.aiImportFile(input_path.encode('utf-8'), 0x8)
    
    if not scene:
        raise Exception("Assimp failed to parse the input file.")
        
    try:
        res = dll.aiExportScene(scene, export_format_id, output_path.encode('utf-8'), 0)
        if res != 0:
            raise Exception(f"Assimp failed to export the scene. Error code: {res}")
    finally:
        dll.aiReleaseImport(scene)
