import os
import hashlib
import subprocess
import threading
from src.backend.ffmpeg_manager import get_local_ffmpeg_exe

CACHE_DIR = os.path.join(os.path.expanduser('~'), '.AnyConverter', 'cache', 'thumbnails')

def _get_cache_path(input_path: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    try:
        mtime = os.path.getmtime(input_path)
    except Exception:
        mtime = 0
    key = f"{input_path}_{mtime}".encode('utf-8')
    file_hash = hashlib.md5(key).hexdigest()
    return os.path.join(CACHE_DIR, f"{file_hash}.png")

def get_thumbnail(input_path: str) -> str | None:
    """Synchronously get or generate a thumbnail for image, pdf, or video files. Returns image path or None."""
    if not input_path or not os.path.exists(input_path):
        return None

    ext = os.path.splitext(input_path)[1].lower().lstrip('.')
    
    # Standard image formats can be returned directly
    if ext in ['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp', 'ico']:
        return input_path
        
    cache_path = _get_cache_path(input_path)
    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
        return cache_path
        
    # High-end/RAW Image thumbnails
    if ext in ['tiff', 'tif', 'raw', 'cr2', 'nef', 'arw', 'dng', 'avif', 'jxl', 'heic', 'heif', 'psd']:
        try:
            ffmpeg_exe = get_local_ffmpeg_exe()
            if ffmpeg_exe:
                cmd = [
                    ffmpeg_exe, "-y",
                    "-i", input_path,
                    "-vframes", "1",
                    "-vf", "scale=256:-1",
                    cache_path
                ]
                res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                if res.returncode == 0 and os.path.exists(cache_path):
                    return cache_path
        except Exception as e:
            print(f"[THUMBNAIL] Error generating High-end Image thumbnail: {e}")

    # PDF & EPUB & eBook thumbnails
    if ext in ['pdf', 'epub', 'mobi', 'azw3', 'azw', 'iba', 'djvu', 'djv', 'chm']:
        try:
            import fitz
            from src.backend.converter import load_ebook_doc
            doc = load_ebook_doc(input_path)
            if len(doc) > 0:
                page = doc.load_page(0)
                rect = page.rect
                zoom = 150.0 / max(rect.width, rect.height, 1)
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                pix.save(cache_path)
                doc.close()
                return cache_path
            doc.close()
        except Exception as e:
            print(f"[THUMBNAIL] Error generating eBook thumbnail: {e}")

    # Video thumbnails
    elif ext in ['mp4', 'mkv', 'avi', 'mov', 'webm', 'wmv', 'flv', 'f4v', 'mxf', 'asf', 'mts', 'm2ts', 'vob', 'ts', '3gp', '3g2', 'ogv', 'rm', 'rmvb', 'm3u8', 'm3u', 'm4s']:
        try:
            ffmpeg_exe = get_local_ffmpeg_exe()
            if ffmpeg_exe:
                # Try seeking to 1 second first, fallback to 0 seconds
                cmd = [
                    ffmpeg_exe, "-y",
                    "-ss", "00:00:01",
                    "-i", input_path,
                    "-vframes", "1",
                    "-vf", "scale=128:-1",
                    cache_path
                ]
                res = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                if res.returncode == 0 and os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
                    return cache_path
                    
                # Retry at 0 seconds for very short videos
                cmd[3] = "00:00:00"
                res = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                if res.returncode == 0 and os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
                    return cache_path
        except Exception as e:
            print(f"[THUMBNAIL] Error generating Video thumbnail: {e}")

    # Audio thumbnails (extract embedded album art if present)
    elif ext in ['mp3', 'wav', 'flac', 'm4a', 'aac', 'ogg', 'aiff', 'alac', 'dff', 'dsf', 'mqa', 'mod', 's3m', 'xm', 'it', 'wma', 'ra', 'bwf', 'amr', 'ac3', 'eac3', 'thd', 'dts', 'dtshd']:
        try:
            ffmpeg_exe = get_local_ffmpeg_exe()
            if ffmpeg_exe:
                cmd = [
                    ffmpeg_exe, "-y",
                    "-i", input_path,
                    "-an",
                    "-vcodec", "mjpeg",
                    "-vf", "scale=128:-1",
                    cache_path
                ]
                res = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                if res.returncode == 0 and os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
                    return cache_path
        except Exception as e:
            print(f"[THUMBNAIL] Error generating Audio thumbnail: {e}")

    # 3D Model thumbnails
    elif ext in ['obj', 'stl', 'ply', 'off', 'dae', 'glb', 'gltf']:
        if _generate_3d_thumbnail(input_path, cache_path):
            return cache_path

    # Vector thumbnails
    elif ext in ['svg']:
        if _generate_vector_thumbnail(input_path, cache_path):
            return cache_path

    return None

def _generate_vector_thumbnail(input_path: str, cache_path: str) -> bool:
    try:
        import fitz  # PyMuPDF
        ext = os.path.splitext(input_path)[1].lower()
        filetype = "pdf" if ext == ".ai" else None
        
        if filetype:
            doc = fitz.open(input_path, filetype=filetype)
        else:
            doc = fitz.open(input_path)
            
        if len(doc) > 0:
            page = doc.load_page(0)
            rect = page.rect
            zoom = 150.0 / max(rect.width, rect.height, 1)
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            pix.save(cache_path)
            doc.close()
            return True
        doc.close()
    except Exception as e:
        print(f"[THUMBNAIL] Error generating Vector thumbnail: {e}")
    return False

def _generate_3d_thumbnail(input_path: str, cache_path: str) -> bool:
    try:
        import trimesh
        import numpy as np
        from PIL import Image, ImageDraw

        loaded = trimesh.load(input_path)
        if isinstance(loaded, trimesh.Scene):
            mesh = loaded.dump(concatenate=True)
        else:
            mesh = loaded

        if not isinstance(mesh, trimesh.Trimesh) or len(mesh.vertices) == 0:
            return False

        vertices = np.asanyarray(mesh.vertices, dtype=np.float32)
        faces = np.asanyarray(mesh.faces, dtype=np.int32)
        if len(faces) == 0:
            return False

        centroid = vertices.mean(axis=0)
        vertices = vertices - centroid
        max_radius = np.max(np.linalg.norm(vertices, axis=1))
        if max_radius > 0:
            vertices = vertices / max_radius

        # Isometric 3D Rotation (-25deg pitch, 45deg yaw)
        rx = np.radians(-25)
        ry = np.radians(45)
        Rx = np.array([[1, 0, 0], [0, np.cos(rx), -np.sin(rx)], [0, np.sin(rx), np.cos(rx)]])
        Ry = np.array([[np.cos(ry), 0, np.sin(ry)], [0, 1, 0], [-np.sin(ry), 0, np.cos(ry)]])
        R = Ry @ Rx

        rot_verts = vertices @ R.T

        v0 = rot_verts[faces[:, 0]]
        v1 = rot_verts[faces[:, 1]]
        v2 = rot_verts[faces[:, 2]]
        normals = np.cross(v1 - v0, v2 - v0)
        norm_lengths = np.linalg.norm(normals, axis=1, keepdims=True)
        norm_lengths[norm_lengths == 0] = 1.0
        normals = normals / norm_lengths

        light_dir = np.array([0.4, 0.6, 0.7])
        light_dir = light_dir / np.linalg.norm(light_dir)
        dots = np.clip(np.dot(normals, light_dir), 0.2, 1.0)

        size = (128, 128)
        w, h = size
        scale = min(w, h) * 0.40
        cx, cy = w / 2.0, h / 2.0
        screen_x = cx + rot_verts[:, 0] * scale
        screen_y = cy - rot_verts[:, 1] * scale

        z_depths = (rot_verts[faces[:, 0], 2] + rot_verts[faces[:, 1], 2] + rot_verts[faces[:, 2], 2]) / 3.0
        sorted_indices = np.argsort(z_depths)

        img = Image.new('RGBA', size, (30, 32, 48, 255))
        draw = ImageDraw.Draw(img)

        # 3D mesh accent color (#ec4899 / pinkish purple)
        r_base, g_base, b_base = 236, 72, 153

        for idx in sorted_indices:
            intensity = dots[idx]
            poly = [
                (screen_x[faces[idx, 0]], screen_y[faces[idx, 0]]),
                (screen_x[faces[idx, 1]], screen_y[faces[idx, 1]]),
                (screen_x[faces[idx, 2]], screen_y[faces[idx, 2]]),
            ]
            col = (int(r_base * intensity), int(g_base * intensity), int(b_base * intensity), 255)
            draw.polygon(poly, fill=col)

        img.save(cache_path, format='PNG')
        return True
    except Exception as e:
        print(f"[THUMBNAIL] Error generating 3D thumbnail: {e}")
        return False

def get_thumbnail_async(input_path: str, callback):
    """Run thumbnail generation in a background thread and invoke callback(thumb_path)."""
    def _worker():
        thumb_path = get_thumbnail(input_path)
        if thumb_path:
            try:
                callback(thumb_path)
            except Exception as e:
                print(f"[THUMBNAIL] Callback error: {e}")
                
    threading.Thread(target=_worker, daemon=True).start()
