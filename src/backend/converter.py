import os
import sys
import subprocess
import threading
from PIL import Image
from src.backend.ffmpeg_manager import get_local_ffmpeg_exe
from src.backend.settings import SettingsManager

def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except Exception:
        try:
            safe_args = [str(a).encode('utf-8', errors='replace').decode('ascii', errors='replace') for a in args]
            print(*safe_args, **kwargs)
        except Exception:
            pass

try:
    import importlib
    _pillow_heif = importlib.import_module('pillow_heif')
    _pillow_heif.register_heif_opener()
except Exception:
    pass


def export_mesh_to_ascii_fbx(mesh, output_fbx_path):
    import numpy as np
    vertices = mesh.vertices.flatten().tolist()
    faces = mesh.faces.tolist()

    poly_indices = []
    for face in faces:
        for i, idx in enumerate(face):
            if i == len(face) - 1:
                poly_indices.append(-int(idx) - 1)
            else:
                poly_indices.append(int(idx))

    v_str = ",".join(f"{val:.6f}" for val in vertices)
    p_str = ",".join(str(idx) for idx in poly_indices)

    num_verts = len(vertices)
    num_indices = len(poly_indices)

    fbx_content = f"""; FBX 7.4.0 project file
FBXHeaderExtension:  {{
	FBXHeaderVersion: 1003
	FBXVersion: 7400
}}

Objects:  {{
	Geometry: 1001, "Geometry::", "Mesh" {{
		Vertices: *{num_verts} {{
			a: {v_str}
		}}
		PolygonVertexIndex: *{num_indices} {{
			a: {p_str}
		}}
		GeometryVersion: 124
	}}
	Model: 1002, "Model::Mesh", "Mesh" {{
		Version: 232
		Properties70:  {{
			P: "InheritType", "enum", "", "",1
		}}
	}}
}}

Connections:  {{
	C: "OO", 1001, 1002
	C: "OO", 1002, 0
}}
"""
    with open(output_fbx_path, 'w', encoding='utf-8') as f:
        f.write(fbx_content)
    return True

def open_eps_preview(file_path):
    import io
    import struct
    import re
    from PIL import Image

    # 1. Try standard Pillow / PyMuPDF opening first
    try:
        img = Image.open(file_path)
        img.load()
        return img
    except Exception:
        pass

    try:
        import fitz
        doc = fitz.open(file_path)
        if len(doc) > 0:
            pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2))
            img_bytes = pix.tobytes("png")
            doc.close()
            return Image.open(io.BytesIO(img_bytes))
    except Exception:
        pass

    # 2. Binary DOS EPS header extraction
    with open(file_path, 'rb') as f:
        header = f.read(30)
        if len(header) >= 30 and header[:4] == b'\xC5\xD0\xD3\xC6':
            ps_start, ps_len, wmf_start, wmf_len, tiff_start, tiff_len, checksum = struct.unpack('<IIIIIIH', header[4:30])
            if tiff_len > 0:
                f.seek(tiff_start)
                tiff_data = f.read(tiff_len)
                return Image.open(io.BytesIO(tiff_data))

        # 3. Fallback: Search raw bytes for embedded TIFF / JPEG streams
        f.seek(0)
        data = f.read()

        tiff_idx = data.find(b'II*\x00')
        if tiff_idx == -1:
            tiff_idx = data.find(b'MM\x00*')
        if tiff_idx != -1:
            try:
                return Image.open(io.BytesIO(data[tiff_idx:]))
            except Exception:
                pass

        jpeg_starts = [m.start() for m in re.finditer(b'\xFF\xD8\xFF', data)]
        for start in jpeg_starts:
            end = data.find(b'\xFF\xD9', start)
            if end != -1:
                try:
                    return Image.open(io.BytesIO(data[start:end+2]))
                except Exception:
                    pass

    raise Exception("Could not open EPS file or extract embedded preview.")

def open_cdr_preview(file_path):
    import io
    import zipfile
    import re
    from PIL import Image

    # 1. Try modern ZIP container (CorelDRAW X4+ / v14+)
    try:
        with zipfile.ZipFile(file_path, 'r') as z:
            candidates = [
                name for name in z.namelist()
                if 'preview' in name.lower() or 'thumbnail' in name.lower() or name.lower().endswith(('.png', '.bmp', '.jpg', '.jpeg'))
            ]
            if candidates:
                best_cand = max(candidates, key=lambda c: z.getinfo(c).file_size)
                img_data = z.read(best_cand)
                return Image.open(io.BytesIO(img_data))
    except Exception:
        pass

    # 2. Search raw bytes for embedded PNG/JPEG/BMP streams in legacy RIFF/OLE CDR files
    with open(file_path, 'rb') as f:
        data = f.read()

    png_idx = data.find(b'\x89PNG\r\n\x1a\n')
    if png_idx != -1:
        png_end = data.find(b'IEND\xaeB`\x82', png_idx)
        if png_end != -1:
            try:
                return Image.open(io.BytesIO(data[png_idx:png_end+8]))
            except Exception:
                pass
        else:
            try:
                return Image.open(io.BytesIO(data[png_idx:]))
            except Exception:
                pass

    jpeg_starts = [m.start() for m in re.finditer(b'\xFF\xD8\xFF', data)]
    for start in jpeg_starts:
        end = data.find(b'\xFF\xD9', start)
        if end != -1:
            try:
                return Image.open(io.BytesIO(data[start:end+2]))
            except Exception:
                pass

    bmp_starts = [m.start() for m in re.finditer(b'BM', data)]
    for start in bmp_starts:
        if start + 14 <= len(data):
            try:
                return Image.open(io.BytesIO(data[start:start+500000]))
            except Exception:
                pass

    raise Exception("Could not extract embedded preview image from CorelDRAW (.cdr) file.")

def palmdoc_decompress(data):
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        byte = data[i]
        i += 1
        if byte == 0:
            out.append(0)
        elif 1 <= byte <= 8:
            out.extend(data[i:i+byte])
            i += byte
        elif 9 <= byte <= 0x7f:
            out.append(byte)
        elif 0x80 <= byte <= 0xbf:
            if i >= n:
                break
            next_b = data[i]
            i += 1
            dist = ((byte & 0x3f) << 5) | (next_b >> 3)
            length = (next_b & 0x07) + 3
            for _ in range(length):
                if dist <= len(out):
                    out.append(out[-dist])
        else:
            out.append(32)
            out.append(byte ^ 0x80)
    return bytes(out)

def unpack_mobi_azw3(file_path):
    import struct
    with open(file_path, "rb") as f:
        data = f.read()
    if len(data) < 78:
        raise Exception("File is too small to be a valid MOBI/AZW3 file.")
    num_records = struct.unpack(">H", data[76:78])[0]
    if num_records == 0:
        raise Exception("MOBI/AZW3 file has no PDB records.")
    record_offsets = []
    for i in range(num_records):
        off = struct.unpack(">I", data[78 + i * 8 : 78 + i * 8 + 4])[0]
        record_offsets.append(off)
    record_offsets.append(len(data))
    rec0 = data[record_offsets[0] : record_offsets[1]]
    if len(rec0) < 10:
        raise Exception("Invalid PalmDOC record header.")
    compression, text_record_count = struct.unpack(">HH", rec0[:4])[0], struct.unpack(">H", rec0[8:10])[0]
    html_parts = []
    for i in range(1, min(text_record_count + 1, num_records)):
        r_start = record_offsets[i]
        r_end = record_offsets[i+1]
        r_data = data[r_start:r_end]
        if compression == 2:
            decomp = palmdoc_decompress(r_data)
        else:
            decomp = r_data
        try:
            html_parts.append(decomp.decode('utf-8', errors='ignore'))
        except Exception:
            html_parts.append(decomp.decode('latin-1', errors='ignore'))
    full_html = "".join(html_parts)
    if not full_html.strip():
        raise Exception("No readable HTML content extracted from MOBI/AZW3 file.")
    return full_html

def unpack_iba(file_path):
    import zipfile
    if not zipfile.is_zipfile(file_path):
        raise Exception("Invalid IBA file: Not a valid ZIP container.")
    with zipfile.ZipFile(file_path, 'r') as z:
        names = z.namelist()
        html_files = [n for n in names if n.lower().endswith(('.html', '.xhtml'))]
        html_files.sort()
        if not html_files:
            raise Exception("IBA archive contains no HTML or XHTML documents.")
        html_chapters = []
        for hf in html_files:
            content = z.read(hf).decode('utf-8', errors='ignore')
            html_chapters.append(content)
    return "<html><body>" + "<hr/>".join(html_chapters) + "</body></html>"

def unpack_fb2(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    return f"<html><body>{content}</body></html>"

def unpack_snb(file_path):
    import zipfile
    import bz2
    import re
    if zipfile.is_zipfile(file_path):
        with zipfile.ZipFile(file_path, 'r') as z:
            names = z.namelist()
            text_files = [n for n in names if n.lower().endswith(('.html', '.xhtml', '.xml', '.txt'))]
            text_files.sort()
            if not text_files:
                raise Exception("SNB archive contains no readable text documents.")
            chapters = []
            for tf in text_files:
                content = z.read(tf).decode('utf-8', errors='ignore')
                if tf.lower().endswith('.txt'):
                    content = f"<pre>{content}</pre>"
                chapters.append(content)
        return "<html><body>" + "<hr/>".join(chapters) + "</body></html>"
        
    with open(file_path, "rb") as f:
        data = f.read()
    
    parts = data.split(b'BZh9')
    text = ""
    for p in parts[1:]:
        chunk = b'BZh9' + p
        try:
            decomp = bz2.decompress(chunk)
            text += decomp.decode('utf-8', errors='ignore') + "\n"
        except Exception:
            pass
            
    if not text.strip():
        strings = re.findall(b'[\x20-\x7E]{4,}', data)
        text = b"\n".join(strings).decode('ascii', errors='ignore')
        
    return f"<html><body><pre>{text}</pre></body></html>"

def unpack_lrf(file_path):
    import re
    with open(file_path, "rb") as f:
        data = f.read()
    strings = re.findall(b'[\x20-\x7E]{4,}', data)
    text = b"\n".join(strings).decode('ascii', errors='ignore')
    return f"<html><body><pre>{text}</pre></body></html>"

def extract_djvu_images(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    if not (data.startswith(b'AT&T') or data.startswith(b'FORM')):
        raise Exception("Invalid DjVu file header.")
    images = []
    idx = 0
    while idx < len(data) - 4:
        if data[idx:idx+3] == b'\xff\xd8\xff':
            j_end = data.find(b'\xff\xd9', idx)
            if j_end != -1:
                images.append(data[idx:j_end+2])
                idx = j_end + 2
                continue
        elif data[idx:idx+4] == b'\x89PNG':
            p_end = data.find(b'IEND', idx)
            if p_end != -1:
                images.append(data[idx:p_end+8])
                idx = p_end + 8
                continue
        idx += 1
    return images

def unpack_chm(file_path):
    import subprocess
    import tempfile
    import shutil
    import os
    
    temp_dir = tempfile.mkdtemp()
    try:
        res = subprocess.run(
            ['hh.exe', '-decompile', temp_dir, file_path],
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        html_content = []
        for root, _, files in os.walk(temp_dir):
            for f in sorted(files):
                if f.lower().endswith(('.htm', '.html')):
                    p = os.path.join(root, f)
                    try:
                        with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                            html_content.append(fp.read())
                    except Exception:
                        pass
        return "<html><body>" + "<hr>".join(html_content) + "</body></html>"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def load_ebook_doc(input_path):
    import fitz
    ext = os.path.splitext(input_path)[1].lower()
    try:
        doc = fitz.open(input_path)
        if len(doc) > 0:
            return doc
        doc.close()
    except Exception:
        pass

    if ext == '.chm':
        html_str = unpack_chm(input_path)
        return fitz.open(stream=html_str.encode('utf-8', errors='ignore'), filetype="html")
    elif ext in ['.mobi', '.azw3', '.azw', '.pdb']:
        html_str = unpack_mobi_azw3(input_path)
        return fitz.open(stream=html_str.encode('utf-8'), filetype="html")
    elif ext == '.iba':
        html_str = unpack_iba(input_path)
        return fitz.open(stream=html_str.encode('utf-8'), filetype="html")
    elif ext == '.snb':
        html_str = unpack_snb(input_path)
        return fitz.open(stream=html_str.encode('utf-8'), filetype="html")
    elif ext in ['.fb2', '.fbz']:
        html_str = unpack_fb2(input_path)
        return fitz.open(stream=html_str.encode('utf-8'), filetype="html")
    elif ext == '.lrf':
        html_str = unpack_lrf(input_path)
        return fitz.open(stream=html_str.encode('utf-8'), filetype="html")
    elif ext in ['.djvu', '.djv']:
        import shutil
        import subprocess
        import tempfile
        ddjvu_exe = shutil.which("ddjvu") or shutil.which("ddjvu.exe")
        if ddjvu_exe:
            temp_pdf = tempfile.mktemp(suffix=".pdf")
            res = subprocess.run([ddjvu_exe, "-format=pdf", input_path, temp_pdf], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            if res.returncode == 0 and os.path.exists(temp_pdf):
                return fitz.open(temp_pdf)
        imgs = extract_djvu_images(input_path)
        if imgs:
            doc = fitz.open()
            for img_bytes in imgs:
                img_doc = fitz.open(stream=img_bytes, filetype="jpg" if img_bytes.startswith(b'\xff\xd8\xff') else "png")
                pdf_bytes = img_doc.convert_to_pdf()
                pdf_page = fitz.open("pdf", pdf_bytes)
                doc.insert_pdf(pdf_page)
                img_doc.close()
                pdf_page.close()
            if len(doc) > 0:
                return doc
        raise Exception("Could not parse DjVu document content.")

    elif ext in ['.cbr', '.cbz', '.cb7', '.cbt']:
        import tempfile
        import shutil
        temp_dir = tempfile.mkdtemp()
        try:
            unpack_archive(input_path, temp_dir)
            image_files = []
            for root, _, files in os.walk(temp_dir):
                for f in files:
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif', '.heic', '.heif')):
                        image_files.append(os.path.join(root, f))
            image_files.sort()
            if not image_files:
                raise Exception("No images found in comic archive.")
                
            doc = fitz.open()
            for img_path in image_files:
                img_doc = fitz.open(img_path)
                pdf_bytes = img_doc.convert_to_pdf()
                pdf_page = fitz.open("pdf", pdf_bytes)
                doc.insert_pdf(pdf_page)
                img_doc.close()
                pdf_page.close()
            return doc
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    raise Exception(f"Unsupported eBook format: {ext}")
def parse_dxf_facets(file_path):
    import trimesh
    vertices = []
    faces = []
    v_map = {}
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = [line.strip() for line in f]
        i = 0
        n = len(lines)
        while i < n:
            if lines[i] == "3DFACE":
                i += 1
                pts = {}
                while i < n and lines[i] != "0":
                    code = lines[i]
                    val = lines[i+1] if i+1 < n else ""
                    i += 2
                    if code in ['10', '20', '30', '11', '21', '31', '12', '22', '32', '13', '23', '33']:
                        pts[code] = float(val)
                if '10' in pts and '20' in pts and '30' in pts:
                    v1 = (pts['10'], pts['20'], pts.get('30', 0.0))
                    v2 = (pts.get('11', v1[0]), pts.get('21', v1[1]), pts.get('31', v1[2]))
                    v3 = (pts.get('12', v2[0]), pts.get('22', v2[1]), pts.get('32', v2[2]))
                    for v in [v1, v2, v3]:
                        if v not in v_map:
                            v_map[v] = len(vertices)
                            vertices.append(v)
                    faces.append([v_map[v1], v_map[v2], v_map[v3]])
            else:
                i += 1
        if vertices and faces:
            return trimesh.Trimesh(vertices=vertices, faces=faces)
    except Exception:
        pass
    return trimesh.load(file_path)

def parse_step_facets(file_path):
    import re
    import trimesh
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    point_pattern = re.compile(r"#(\d+)\s*=\s*CARTESIAN_POINT\s*\(\s*'.*?'\s*,\s*\(\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)\s*\)\s*\)")
    points = {}
    for match in point_pattern.finditer(content):
        pid = int(match.group(1))
        x, y, z = float(match.group(2)), float(match.group(3)), float(match.group(4))
        points[pid] = (x, y, z)
    if not points:
        return trimesh.load(file_path)
class SubtitleItem:
    def __init__(self, start_ms, end_ms, text):
        self.start_ms = start_ms
        self.end_ms = end_ms
        self.text = text

def ms_to_srt_time(ms):
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    ms %= 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def ms_to_vtt_time(ms):
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    ms %= 1000
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

def ms_to_ass_time(ms):
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    cs = ms // 10
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def parse_time_to_ms(time_str):
    time_str = time_str.replace(',', '.').strip()
    parts = time_str.split(':')
    if len(parts) == 3:
        h = int(parts[0])
        m = int(parts[1])
        s_parts = parts[2].split('.')
        s = int(s_parts[0])
        ms = int(s_parts[1].ljust(3, '0')[:3]) if len(s_parts) > 1 else 0
        return h * 3600000 + m * 60000 + s * 1000 + ms
    elif len(parts) == 2:
        m = int(parts[0])
        s_parts = parts[1].split('.')
        s = int(s_parts[0])
        ms = int(s_parts[1].ljust(3, '0')[:3]) if len(s_parts) > 1 else 0
        return m * 60000 + s * 1000 + ms
    return 0

def parse_subtitle(file_path):
    import os
    ext = os.path.splitext(file_path)[1].lower()
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    items = []
    content_clean = content.replace('\r\n', '\n')

    if ext in ['.srt', '.vtt']:
        blocks = content_clean.strip().split('\n\n')
        for block in blocks:
            lines = [l.strip() for l in block.strip().split('\n') if l.strip()]
            for idx, l in enumerate(lines):
                if '-->' in l:
                    times = l.split('-->')
                    start_ms = parse_time_to_ms(times[0])
                    end_ms = parse_time_to_ms(times[1].split()[0])
                    text = "\n".join(lines[idx+1:])
                    items.append(SubtitleItem(start_ms, end_ms, text))
                    break

    elif ext in ['.ass', '.ssa']:
        for line in content_clean.split('\n'):
            if line.startswith('Dialogue:'):
                parts = line.split(',', 9)
                if len(parts) >= 10:
                    start_ms = parse_time_to_ms(parts[1])
                    end_ms = parse_time_to_ms(parts[2])
                    text = parts[9].replace('\\N', '\n').replace('\\n', '\n')
                    items.append(SubtitleItem(start_ms, end_ms, text))

    elif ext == '.sub':
        import re
        microdvd_re = re.compile(r"\{(\d+)\}\{(\d+)\}(.*)")
        for line in content_clean.split('\n'):
            line = line.strip()
            match = microdvd_re.match(line)
            if match:
                f_start = int(match.group(1))
                f_end = int(match.group(2))
                text = match.group(3).replace('|', '\n')
                # Assume 24 fps
                items.append(SubtitleItem(int(f_start * 1000 / 24), int(f_end * 1000 / 24), text))
            elif '-->' in line or ',' in line:
                parts = line.split(',')
                if len(parts) >= 2 and parse_time_to_ms(parts[0]) > 0:
                    start_ms = parse_time_to_ms(parts[0])
                    end_ms = parse_time_to_ms(parts[1])
                    items.append(SubtitleItem(start_ms, end_ms, ""))

    elif ext == '.scc':
        for line in content_clean.split('\n'):
            line = line.strip()
            if '\t' in line or ' ' in line:
                parts = line.replace('\t', ' ').split(maxsplit=1)
                if len(parts) == 2 and ':' in parts[0]:
                    start_ms = parse_time_to_ms(parts[0])
                    items.append(SubtitleItem(start_ms, start_ms + 3000, parts[1]))

    else:
        # Generic text transcript
        lines = [l.strip() for l in content_clean.split('\n') if l.strip()]
        for i, l in enumerate(lines):
            items.append(SubtitleItem(i * 3000, (i + 1) * 3000, l))

    return items

def export_subtitle(items, target_format):
    fmt = target_format.lower().lstrip('.')

    if fmt == 'vtt':
        out = ["WEBVTT\n"]
        for i, item in enumerate(items, 1):
            out.append(f"{i}\n{ms_to_vtt_time(item.start_ms)} --> {ms_to_vtt_time(item.end_ms)}\n{item.text}\n")
        return "\n".join(out)

    elif fmt == 'ass' or fmt == 'ssa':
        header = "[Script Info]\nScriptType: v4.00+\nPlayResX: 384\nPlayResY: 288\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        out = [header]
        for item in items:
            text_ass = item.text.replace('\n', '\\N')
            out.append(f"Dialogue: 0,{ms_to_ass_time(item.start_ms)},{ms_to_ass_time(item.end_ms)},Default,,0,0,0,,{text_ass}")
        return "\n".join(out)

    elif fmt == 'sub':
        out = []
        for item in items:
            f_start = int(item.start_ms * 24 / 1000)
            f_end = int(item.end_ms * 24 / 1000)
            text_sub = item.text.replace('\n', '|')
            out.append(f"{{{f_start}}}{{{f_end}}}{text_sub}")
        return "\n".join(out)

    elif fmt == 'scc':
        out = ["Scenarist_SCC V1.0\n"]
        for item in items:
            out.append(f"{ms_to_srt_time(item.start_ms)}\t{item.text.replace('\n', ' ')}")
        return "\n".join(out)

    elif fmt == 'txt':
        return "\n".join(item.text for item in items)

    else:
        # Default to SRT
        out = []
        for i, item in enumerate(items, 1):
            out.append(f"{i}\n{ms_to_srt_time(item.start_ms)} --> {ms_to_srt_time(item.end_ms)}\n{item.text}\n")
        return "\n".join(out)

def parse_database(file_path):
    import sqlite3
    import os
    import json
    import re
    
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in ['.sqlite', '.sqlite3', '.db']:
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall() if row[0] != 'sqlite_sequence']
        db_dict = {}
        for t in tables:
            cursor.execute(f"SELECT * FROM `{t}`")
            cols = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            db_dict[t] = [dict(zip(cols, r)) for r in rows]
        conn.close()
        return db_dict
        
    elif ext == '.sql':
        conn = sqlite3.connect(":memory:")
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            sql_script = f.read()
        try:
            conn.executescript(sql_script)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall() if row[0] != 'sqlite_sequence']
            db_dict = {}
            for t in tables:
                cursor.execute(f"SELECT * FROM `{t}`")
                cols = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                db_dict[t] = [dict(zip(cols, r)) for r in rows]
            conn.close()
            return db_dict
        except Exception:
            conn.close()
            # Regex fallback for INSERT INTO statements
            inserts = re.findall(r"INSERT\s+INTO\s+[`\"']?(\w+)[`\"']?\s*(?:\(([^)]+)\))?\s*VALUES\s*(.+?);", sql_script, re.IGNORECASE)
            db_dict = {}
            for table, cols_str, vals_str in inserts:
                if table not in db_dict: db_dict[table] = []
                cols = [c.strip(" `\"'") for c in cols_str.split(',')] if cols_str else []
                # Simple value extractor
                val_tuples = re.findall(r"\(([^)]+)\)", vals_str)
                for vt in val_tuples:
                    vals = [v.strip(" '\"") for v in vt.split(',')]
                    if cols and len(cols) == len(vals):
                        db_dict[table].append(dict(zip(cols, vals)))
                    else:
                        db_dict[table].append({f"col_{idx+1}": v for idx, v in enumerate(vals)})
            return db_dict
            
    elif ext in ['.mdb', '.accdb']:
        try:
            import win32com.client
            db_dict = {}
            engine = win32com.client.Dispatch("DAO.DBEngine.36") if ext == '.mdb' else win32com.client.Dispatch("DAO.DBEngine.120")
            db = engine.OpenDatabase(file_path)
            for t in db.TableDefs:
                if not t.Name.startswith("MSys"):
                    rs = db.OpenRecordset(t.Name)
                    rows = []
                    cols = [field.Name for field in rs.Fields]
                    while not rs.EOF:
                        row = [rs.Fields(i).Value for i in range(rs.Fields.Count)]
                        rows.append(dict(zip(cols, row)))
                        rs.MoveNext()
                    db_dict[t.Name] = rows
            db.Close()
            return db_dict
        except Exception:
            raise Exception("Microsoft Access database driver not installed or requires Office Access DAO components.")
            
    return {}

def export_database(data_dict, target_fmt, output_path):
    import sqlite3
    import json
    import yaml
    import csv
    import xmltodict
    import os
    
    fmt = target_fmt.lower().lstrip('.')
    
    if fmt in ['sqlite', 'sqlite3', 'db']:
        if os.path.exists(output_path): os.remove(output_path)
        conn = sqlite3.connect(output_path)
        cursor = conn.cursor()
        if isinstance(data_dict, dict):
            for tname, rows in data_dict.items():
                if isinstance(rows, list) and rows and isinstance(rows[0], dict):
                    cols = list(rows[0].keys())
                    col_defs = ", ".join(f"`{c}` TEXT" for c in cols)
                    cursor.execute(f"CREATE TABLE `{tname}` ({col_defs});")
                    placeholders = ", ".join("?" for _ in cols)
                    for r in rows:
                        vals = [str(r.get(c, '')) for c in cols]
                        cursor.execute(f"INSERT INTO `{tname}` VALUES ({placeholders})", vals)
        conn.commit()
        conn.close()
        
    elif fmt == 'sql':
        lines = []
        if isinstance(data_dict, dict):
            for tname, rows in data_dict.items():
                if isinstance(rows, list) and rows and isinstance(rows[0], dict):
                    cols = list(rows[0].keys())
                    col_defs = ", ".join(f"`{c}` TEXT" for c in cols)
                    lines.append(f"CREATE TABLE IF NOT EXISTS `{tname}` ({col_defs});")
                    for r in rows:
                        vals_str = ", ".join("'" + str(r.get(c, '')).replace("'", "''") + "'" for c in cols)
                        cols_str = ", ".join(f"`{c}`" for c in cols)
                        lines.append(f"INSERT INTO `{tname}` ({cols_str}) VALUES ({vals_str});")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
            
    elif fmt == 'json':
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data_dict, f, indent=2)
            
    elif fmt in ['yaml', 'yml']:
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(data_dict, f, default_flow_style=False, sort_keys=False)
            
    elif fmt == 'csv':
        # Grab first table or flat list
        rows = list(data_dict.values())[0] if isinstance(data_dict, dict) and data_dict else data_dict
        if isinstance(rows, list) and rows and isinstance(rows[0], dict):
            headers = sorted(list(set().union(*(r.keys() for r in rows if isinstance(r, dict)))))
            with open(output_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                for r in rows:
                    if isinstance(r, dict): writer.writerow(r)
                    
    elif fmt == 'xml':
        xml_str = xmltodict.unparse({'database': data_dict}, pretty=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(xml_str)


def parse_gis(file_path):
    import os
    import json
    import zipfile
    import xml.etree.ElementTree as ET
    
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in ['.geojson', '.json']:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return json.load(f)
            
    elif ext == '.kml':
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return parse_kml_content(content)
        
    elif ext == '.kmz':
        with zipfile.ZipFile(file_path, 'r') as zf:
            for name in zf.namelist():
                if name.endswith('.kml'):
                    content = zf.read(name).decode('utf-8', errors='ignore')
                    return parse_kml_content(content)
                    
    elif ext == '.gpx':
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        root = ET.fromstring(content)
        features = []
        ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
        wpts = root.findall('.//gpx:wpt', ns) or root.findall('.//wpt')
        for wpt in wpts:
            lat = float(wpt.attrib.get('lat', 0.0))
            lon = float(wpt.attrib.get('lon', 0.0))
            name_e = wpt.find('gpx:name', ns) or wpt.find('name')
            name = name_e.text if name_e is not None else ""
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {"name": name}
            })
        return {"type": "FeatureCollection", "features": features}
        
    return {"type": "FeatureCollection", "features": []}

def parse_kml_content(content):
    import xml.etree.ElementTree as ET
    root = ET.fromstring(content)
    namespaces = {'kml': 'http://www.opengis.net/kml/2.2'}
    placemarks = root.findall('.//kml:Placemark', namespaces) or root.findall('.//Placemark')
    features = []
    for pm in placemarks:
        name_e = pm.find('kml:name', namespaces) or pm.find('name')
        name = name_e.text if name_e is not None else ""
        coord_e = pm.find('.//kml:coordinates', namespaces) or pm.find('.//coordinates')
        if coord_e is not None and coord_e.text:
            coords_raw = coord_e.text.strip().split()
            if len(coords_raw) == 1:
                parts = coords_raw[0].split(',')
                if len(parts) >= 2:
                    lon, lat = float(parts[0]), float(parts[1])
                    features.append({
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [lon, lat]},
                        "properties": {"name": name}
                    })
    return {"type": "FeatureCollection", "features": features}

def export_gis(geojson_dict, target_fmt, output_path):
    import json
    import csv
    
    fmt = target_fmt.lower().lstrip('.')
    features = geojson_dict.get("features", [])
    
    if fmt in ['geojson', 'json']:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(geojson_dict, f, indent=2)
            
    elif fmt == 'kml':
        lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>']
        for f in features:
            geom = f.get("geometry", {})
            name = f.get("properties", {}).get("name", "")
            if geom.get("type") == "Point":
                coords = geom.get("coordinates", [0, 0])
                lines.append(f'  <Placemark><name>{name}</name><Point><coordinates>{coords[0]},{coords[1]},0</coordinates></Point></Placemark>')
        lines.append('</Document></kml>')
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
            
    elif fmt == 'gpx':
        lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<gpx version="1.1" creator="AnyConverter">']
        for f in features:
            geom = f.get("geometry", {})
            name = f.get("properties", {}).get("name", "")
            if geom.get("type") == "Point":
                coords = geom.get("coordinates", [0, 0])
                lines.append(f'  <wpt lat="{coords[1]}" lon="{coords[0]}"><name>{name}</name></wpt>')
        lines.append('</gpx>')
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
            
    elif fmt == 'csv':
        rows = []
        for f in features:
            geom = f.get("geometry", {})
            props = f.get("properties", {})
            row = dict(props)
            if geom.get("type") == "Point":
                coords = geom.get("coordinates", [0, 0])
                row['longitude'] = coords[0]
                row['latitude'] = coords[1]
            rows.append(row)
        headers = sorted(list(set().union(*(r.keys() for r in rows)))) if rows else ['name', 'latitude', 'longitude']
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
def unpack_archive(input_path, extract_dir):
    import zipfile
    import tarfile
    import py7zr
    import shutil
    import os
    
    ext = os.path.splitext(input_path)[1].lower()
    filename = os.path.basename(input_path).lower()
    
    if filename.endswith('.tar.gz') or filename.endswith('.tgz') or filename.endswith('.tar.bz2') or filename.endswith('.tar.xz'):
        with tarfile.open(input_path, 'r:*') as tf:
            tf.extractall(extract_dir)
        return

    if ext == '.zip':
        with zipfile.ZipFile(input_path, 'r') as zf:
            zf.extractall(extract_dir)
    elif ext in ['.tar', '.gz', '.bz2', '.xz']:
        with tarfile.open(input_path, 'r:*') as tf:
            tf.extractall(extract_dir)
    elif ext == '.7z':
        with py7zr.SevenZipFile(input_path, 'r') as sz:
            sz.extractall(extract_dir)
    elif ext == '.iso':
        import pycdlib
        iso = pycdlib.PyCdlib()
        iso.open(input_path)
        for dirname, dirnames, filenames in iso.walk(iso_path='/'):
            local_dir = os.path.join(extract_dir, dirname.lstrip('/'))
            os.makedirs(local_dir, exist_ok=True)
            for f in filenames:
                iso_file_path = dirname + '/' + f if dirname != '/' else '/' + f
                clean_f = f.split(';')[0] if ';' in f else f
                out_file = os.path.join(local_dir, clean_f)
                iso.get_file_from_iso(out_file, iso_path=iso_file_path)
        iso.close()
    else:
        seven_zip_exe = shutil.which("7z") or shutil.which("7z.exe") or shutil.which("7za")
        if seven_zip_exe:
            import subprocess
            res = subprocess.run([seven_zip_exe, "x", input_path, f"-o{extract_dir}", "-y"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            if res.returncode == 0:
                return
        try:
            with py7zr.SevenZipFile(input_path, 'r') as sz:
                sz.extractall(extract_dir)
                return
        except Exception:
            pass
        raise Exception(f"Archive / Disk Image format {ext} requires 7-Zip component to extract.")

def pack_archive(source_dir, output_path, target_fmt):
    import zipfile
    import tarfile
    import py7zr
    import os
    
    target_fmt = target_fmt.lower().lstrip('.')
    
    if target_fmt == 'zip':
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    full = os.path.join(root, file)
                    rel = os.path.relpath(full, source_dir)
                    zf.write(full, arcname=rel)
                    
    elif target_fmt == '7z':
        with py7zr.SevenZipFile(output_path, 'w') as sz:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    full = os.path.join(root, file)
                    rel = os.path.relpath(full, source_dir)
                    sz.write(full, arcname=rel)
                    
    elif target_fmt == 'iso':
        import pycdlib
        iso = pycdlib.PyCdlib()
        iso.new(interchange_level=3, joliet=3)
        # Pycdlib requires adding directories first, parent before child.
        # os.walk is top-down by default, so it's perfectly ordered.
        for root, dirs, files in os.walk(source_dir):
            for dirname in dirs:
                full_dir = os.path.join(root, dirname)
                rel_dir = os.path.relpath(full_dir, source_dir).replace('\\', '/')
                iso.add_directory(joliet_path='/' + rel_dir)
            for file in files:
                full = os.path.join(root, file)
                rel = os.path.relpath(full, source_dir).replace('\\', '/')
                iso.add_file(full, joliet_path='/' + rel)
        iso.write(output_path)
        iso.close()
                    
    elif target_fmt in ['tar', 'tar.gz', 'tgz', 'tar.bz2', 'tar.xz']:
        mode = "w"
        if target_fmt in ['tar.gz', 'tgz']: mode = "w:gz"
        elif target_fmt == 'tar.bz2': mode = "w:bz2"
        elif target_fmt == 'tar.xz': mode = "w:xz"
        
        with tarfile.open(output_path, mode) as tf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    full = os.path.join(root, file)
                    rel = os.path.relpath(full, source_dir)
                    tf.add(full, arcname=rel)
def pdf_to_epub(input_path_or_doc, epub_path, title=None, author="Any Converter"):
    import html
    import uuid
    import zipfile
    import fitz

    if isinstance(input_path_or_doc, str):
        ext = os.path.splitext(input_path_or_doc)[1].lower()
        if ext == '.pdf':
            doc = fitz.open(input_path_or_doc)
        else:
            doc = load_ebook_doc(input_path_or_doc)
        should_close = True
        base_name = os.path.splitext(os.path.basename(input_path_or_doc))[0]
    else:
        doc = input_path_or_doc
        should_close = False
        base_name = "Converted Document"

    try:
        if not title:
            meta_title = doc.metadata.get('title') if hasattr(doc, 'metadata') and doc.metadata else None
            if meta_title and meta_title.strip():
                title = meta_title.strip()
            else:
                title = base_name

        meta_author = doc.metadata.get('author') if hasattr(doc, 'metadata') and doc.metadata else None
        if meta_author and meta_author.strip():
            author = meta_author.strip()

        book_id = f"urn:uuid:{uuid.uuid4()}"
        manifest_items = []
        spine_items = []
        nav_points = []

        with zipfile.ZipFile(epub_path, 'w') as zip_epub:
            # 1. mimetype (MUST be first file, uncompressed)
            zip_epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)

            # 2. META-INF/container.xml
            container_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''
            zip_epub.writestr('META-INF/container.xml', container_xml, compress_type=zipfile.ZIP_DEFLATED)

            # 3. OEBPS/style.css
            css_content = '''@charset "utf-8";
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
    margin: 5% 8%;
    color: #1a1a1a;
    background-color: #ffffff;
}
h1, h2, h3, h4, h5, h6 {
    line-height: 1.25;
    margin-top: 1.4em;
    margin-bottom: 0.5em;
    font-weight: 600;
}
p {
    margin-top: 0;
    margin-bottom: 1em;
    text-align: justify;
}
img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1.5em auto;
}
.image-wrapper {
    text-align: center;
    margin: 1.5em 0;
}
.page-container {
    page-break-after: always;
    margin-bottom: 2em;
}
.page-number {
    font-size: 0.8em;
    color: #888888;
    text-align: center;
    margin-top: 2em;
    border-top: 1px solid #eeeeee;
    padding-top: 0.5em;
}
'''
            zip_epub.writestr('OEBPS/style.css', css_content, compress_type=zipfile.ZIP_DEFLATED)
            manifest_items.append('<item id="style" href="style.css" media-type="text/css"/>')

            image_count = 0

            # 4. Iterate over pages
            for page_idx in range(len(doc)):
                page = doc.load_page(page_idx)
                page_num = page_idx + 1
                page_id = f"page_{page_num}"
                page_filename = f"{page_id}.xhtml"

                blocks = page.get_text("blocks")
                page_html_parts = []
                has_text = False

                for b in blocks:
                    if b[6] == 0:  # Text block
                        text = b[4].strip()
                        if text:
                            has_text = True
                            paras = text.split('\n\n')
                            for p in paras:
                                p_clean = p.replace('\n', ' ').strip()
                                if p_clean:
                                    if len(p_clean) < 80 and (b[3] - b[1] > 18 or p_clean.isupper()):
                                        page_html_parts.append(f"<h2>{html.escape(p_clean)}</h2>")
                                    else:
                                        page_html_parts.append(f"<p>{html.escape(p_clean)}</p>")

                # Extract embedded images
                try:
                    img_list = page.get_images(full=True)
                except Exception:
                    img_list = []

                for img_info in img_list:
                    try:
                        xref = img_info[0]
                        base_image = doc.extract_image(xref)
                        if base_image:
                            image_bytes = base_image["image"]
                            image_ext = base_image["ext"].lower()
                            if image_ext in ['jpg', 'jpeg', 'png', 'webp']:
                                image_count += 1
                                img_id = f"img_{image_count}"
                                img_filename = f"images/{img_id}.{image_ext}"
                                mime_type = f"image/{'jpeg' if image_ext in ['jpg', 'jpeg'] else image_ext}"

                                zip_epub.writestr(f"OEBPS/{img_filename}", image_bytes, compress_type=zipfile.ZIP_DEFLATED)
                                manifest_items.append(f'<item id="{img_id}" href="{img_filename}" media-type="{mime_type}"/>')
                                page_html_parts.append(f'<div class="image-wrapper"><img src="{img_filename}" alt="Image {image_count}"/></div>')
                    except Exception:
                        pass

                # Fallback for scanned pages or graphic-only pages
                if not has_text and not img_list:
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    image_count += 1
                    img_id = f"img_page_{page_num}"
                    img_filename = f"images/{img_id}.png"
                    zip_epub.writestr(f"OEBPS/{img_filename}", pix.tobytes("png"), compress_type=zipfile.ZIP_DEFLATED)
                    manifest_items.append(f'<item id="{img_id}" href="{img_filename}" media-type="image/png"/>')
                    page_html_parts.append(f'<div class="image-wrapper"><img src="{img_filename}" alt="Page {page_num}"/></div>')

                page_content = "\n        ".join(page_html_parts)
                xhtml_doc = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en">
<head>
    <meta charset="utf-8"/>
    <title>{html.escape(title)} - Page {page_num}</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <section class="page-container" epub:type="chapter">
        {page_content}
        <div class="page-number">{page_num}</div>
    </section>
</body>
</html>'''
                zip_epub.writestr(f"OEBPS/{page_filename}", xhtml_doc, compress_type=zipfile.ZIP_DEFLATED)
                manifest_items.append(f'<item id="{page_id}" href="{page_filename}" media-type="application/xhtml+xml"/>')
                spine_items.append(f'<itemref idref="{page_id}"/>')
                nav_points.append(f'''    <navPoint id="nav_{page_id}" playOrder="{page_num}">
        <navLabel><text>Page {page_num}</text></navLabel>
        <content src="{page_filename}"/>
    </navPoint>''')

            # 5. OEBPS/toc.ncx (EPUB 2 compatibility)
            ncx_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content="{book_id}"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="{len(doc)}"/>
        <meta name="dtb:maxPageNumber" content="{len(doc)}"/>
    </head>
    <docTitle><text>{html.escape(title)}</text></docTitle>
    <docAuthor><text>{html.escape(author)}</text></docAuthor>
    <navMap>
{chr(10).join(nav_points)}
    </navMap>
</ncx>'''
            zip_epub.writestr('OEBPS/toc.ncx', ncx_content, compress_type=zipfile.ZIP_DEFLATED)
            manifest_items.append('<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>')

            # 6. OEBPS/nav.xhtml (EPUB 3 Navigation Document)
            nav_list_items = [f'<li><a href="{page_id}.xhtml">Page {i + 1}</a></li>' for i, page_id in enumerate([f"page_{p+1}" for p in range(len(doc))])]
            nav_xhtml = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en">
<head>
    <meta charset="utf-8"/>
    <title>Table of Contents</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <nav epub:type="toc" id="toc">
        <h1>Table of Contents</h1>
        <ol>
            {chr(10).join(nav_list_items)}
        </ol>
    </nav>
</body>
</html>'''
            zip_epub.writestr('OEBPS/nav.xhtml', nav_xhtml, compress_type=zipfile.ZIP_DEFLATED)
            manifest_items.append('<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>')

            # 7. OEBPS/content.opf
            manifest_str = "\n        ".join(manifest_items)
            spine_str = "\n        ".join(spine_items)

            content_opf = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookID" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
        <dc:title>{html.escape(title)}</dc:title>
        <dc:creator>{html.escape(author)}</dc:creator>
        <dc:language>en</dc:language>
        <dc:identifier id="BookID">{book_id}</dc:identifier>
        <meta property="dcterms:modified">2026-08-18T12:00:00Z</meta>
    </metadata>
    <manifest>
        {manifest_str}
    </manifest>
    <spine toc="ncx">
        {spine_str}
    </spine>
</package>'''
            zip_epub.writestr('OEBPS/content.opf', content_opf, compress_type=zipfile.ZIP_DEFLATED)
    finally:
        if should_close:
            doc.close()

def resolve_unique_path(output_dir, base_name, target_ext, src_ext=None, existing_claimed_paths=None, input_path=None):
    """
    Generates a collision-free output path in output_dir.
    Checks before saving if any same name file exists in the destination folder or
    is claimed by another active job.
    If 'base_name.target_ext' does not exist in the folder (and is not the source input file,
    and not claimed), it returns 'base_name.target_ext' WITHOUT any (1) number.
    If a file with the same name already exists in the folder (or is claimed / is the input file),
    it disambiguates by appending ' (1)', ' (2)', etc.
    """
    target_ext = target_ext.lstrip('.').lower().strip()
    candidate = os.path.join(output_dir, f"{base_name}.{target_ext}")
    
    def norm(p):
        return os.path.normcase(os.path.abspath(p)) if p else ""

    claimed_set = {norm(p) for p in existing_claimed_paths if p} if existing_claimed_paths else set()
    norm_input = norm(input_path) if input_path else ""

    def is_taken(p):
        norm_p = norm(p)
        if norm_p in claimed_set:
            return True
        if norm_input and norm_p == norm_input:
            return True
        if os.path.exists(p):
            return True
        return False

    if not is_taken(candidate):
        return candidate
        
    # Append (1), (2), (3), ...
    counter = 1
    while True:
        cand_num = os.path.join(output_dir, f"{base_name} ({counter}).{target_ext}")
        if not is_taken(cand_num):
            return cand_num
        counter += 1

def save_cur(im, filepath, hotspot=(0, 0)):
    im = im.convert('RGBA')
    w, h = im.size
    if w > 256 or h > 256:
        im = im.resize((32, 32), Image.Resampling.LANCZOS)
        w, h = 32, 32
    xor_bytes = bytearray()
    for y in reversed(range(h)):
        for x in range(w):
            r, g, b, a = im.getpixel((x, y))
            xor_bytes.extend([b, g, r, a])
    row_bytes_len = (w + 31) // 32 * 4
    and_bytes = bytearray()
    for y in reversed(range(h)):
        row = bytearray(row_bytes_len)
        for x in range(w):
            _, _, _, a = im.getpixel((x, y))
            if a < 128:
                row[x // 8] |= (1 << (7 - (x % 8)))
        and_bytes.extend(row)
    import struct
    bih = struct.pack('<IIIHHIIIIII', 40, w, 2 * h, 1, 32, 0, len(xor_bytes) + len(and_bytes), 0, 0, 0, 0)
    image_data = bih + xor_bytes + and_bytes
    dir_entry = struct.pack('<BBBBHHII', w if w < 256 else 0, h if h < 256 else 0, 0, 0, hotspot[0], hotspot[1], len(image_data), 6 + 16)
    header = struct.pack('<HHH', 0, 2, 1)
    with open(filepath, 'wb') as f:
        f.write(header + dir_entry + image_data)

def save_xpm(im, filepath):
    im = im.convert('RGB')
    w, h = im.size
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+[]{}|;:,.<>?'
    im_q = im.quantize(colors=min(64, len(chars)))
    palette = im_q.getpalette()
    num_colors = min(64, len(palette) // 3)
    color_map = {}
    for i in range(num_colors):
        r, g, b = palette[i*3], palette[i*3+1], palette[i*3+2]
        color_map[i] = (chars[i], f'#{r:02x}{g:02x}{b:02x}')
    with open(filepath, 'w', encoding='ascii') as f:
        f.write('/* XPM */\nstatic char *image[] = {\n')
        f.write(f'"{w} {h} {num_colors} 1",\n')
        for i in range(num_colors):
            sym, hex_c = color_map[i]
            f.write(f'"{sym} c {hex_c}",\n')
        pixels = im_q.load()
        for y in range(h):
            row = ''.join(color_map[pixels[x, y]][0] for x in range(w))
            comma = ',' if y < h - 1 else ''
            f.write(f'"{row}"{comma}\n')
        f.write('};\n')

class ConversionJob:
    def __init__(self, input_path, target_format, output_dir=None, existing_claimed_paths=None):
        self.input_path = input_path
        self.target_format = target_format.lower()
        self._explicit_output_dir = output_dir is not None
        
        settings = SettingsManager()
        self.output_dir = output_dir or settings.get('output_dir') or os.path.dirname(input_path)
        
        filename = os.path.basename(input_path)
        name, src_ext = os.path.splitext(filename)
        self.src_ext = src_ext
        self.output_path = resolve_unique_path(
            self.output_dir,
            name,
            self.target_format,
            src_ext=src_ext,
            existing_claimed_paths=existing_claimed_paths,
            input_path=self.input_path
        )
        
        self.status = "Pending"
        self.progress = 0
        self.error_message = None

    def _convert_image(self):
        try:
            target_fmt = self.target_format.lower().strip()
            os.makedirs(self.output_dir, exist_ok=True)
            input_ext = os.path.splitext(self.input_path)[1].lower()
            if input_ext in ['.eps', '.ps']:
                img = open_eps_preview(self.input_path)
            elif input_ext == '.cdr':
                img = open_cdr_preview(self.input_path)
            elif input_ext in ['.raw', '.cr2', '.nef', '.arw', '.dng', '.raf', '.pef']:
                try:
                    import rawpy
                    with rawpy.imread(self.input_path) as raw:
                        rgb = raw.postprocess()
                        img = Image.fromarray(rgb)
                except ImportError:
                    raise Exception("RAW image conversion requires the 'rawpy' module. Please run: pip install rawpy")
            elif input_ext == '.psd':
                try:
                    from psd_tools import PSDImage
                    psd = PSDImage.open(self.input_path)
                    img = psd.composite()
                except ImportError:
                    raise Exception("PSD image conversion requires the 'psd-tools' module. Please run: pip install psd-tools")
            else:
                try:
                    img = Image.open(self.input_path)
                except Exception as pil_open_err:
                    # If Pillow fails to open (e.g. OpenEXR .exr, .dpx, exotic encodings), decode via FFmpeg pipe into Pillow Image!
                    ffmpeg_exe = get_local_ffmpeg_exe()
                    if not ffmpeg_exe:
                        raise pil_open_err
                    cmd = [ffmpeg_exe, "-y", "-i", self.input_path, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"]
                    pipe_res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                    if pipe_res.returncode == 0 and pipe_res.stdout:
                        import io
                        img = Image.open(io.BytesIO(pipe_res.stdout))
                    else:
                        raise pil_open_err
            
            try:
                # Handle alpha channel & mode conversions appropriately
                if target_fmt in ['jpg', 'jpeg', 'bmp', 'pcx', 'ppm', 'pgm', 'pbm', 'pnm', 'sgi', 'dib']:
                    # JPEG, BMP, DIB, PCX, PPM do not support alpha transparency or paletted modes directly
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        bg = Image.new('RGB', img.size, (255, 255, 255))
                        rgba = img.convert('RGBA')
                        bg.paste(rgba, mask=rgba.split()[3])
                        img = bg
                    elif img.mode not in ('RGB', 'L'):
                        img = img.convert('RGB')
                elif target_fmt in ['tiff', 'tif']:
                    if img.mode not in ('RGB', 'RGBA', 'L', 'CMYK'):
                        img = img.convert('RGBA' if 'transparency' in img.info or img.mode in ('RGBA', 'LA') else 'RGB')
                elif target_fmt == 'png':
                    if img.mode not in ('RGB', 'RGBA', 'L', '1', 'P'):
                        img = img.convert('RGBA')
                elif target_fmt == 'webp':
                    if img.mode not in ('RGB', 'RGBA'):
                        img = img.convert('RGBA' if 'transparency' in img.info or img.mode in ('RGBA', 'LA') else 'RGB')
                elif target_fmt == 'gif':
                    if img.mode not in ('P', 'L'):
                        img = img.convert('P')
                elif target_fmt in ['heic', 'heif', 'avif']:
                    if img.mode not in ('RGB', 'RGBA'):
                        img = img.convert('RGB')

                # Determine Pillow format code
                if target_fmt == 'jpg':
                    pil_fmt = 'jpeg'
                elif target_fmt in ['tiff', 'tif']:
                    pil_fmt = 'TIFF'
                elif target_fmt in ['heic', 'heif']:
                    pil_fmt = 'HEIF'
                elif target_fmt in ['ppm', 'pgm', 'pbm', 'pnm']:
                    pil_fmt = 'PPM'
                elif target_fmt == 'ico':
                    pil_fmt = 'ICO'
                elif target_fmt == 'dib':
                    pil_fmt = 'DIB'
                else:
                    pil_fmt = target_fmt.upper()
                
                if target_fmt == 'ico':
                    img.save(self.output_path, format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
                elif target_fmt == 'cur':
                    save_cur(img, self.output_path)
                elif target_fmt == 'xpm':
                    save_xpm(img, self.output_path)
                elif target_fmt == 'xbm':
                    img.convert('1').save(self.output_path, format='XBM')
                elif target_fmt == 'svg':
                    import base64
                    import io
                    buf = io.BytesIO()
                    img.save(buf, format='PNG')
                    b64_str = base64.b64encode(buf.getvalue()).decode('ascii')
                    w, h = img.size
                    svg_content = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><image width="{w}" height="{h}" href="data:image/png;base64,{b64_str}"/></svg>'
                    with open(self.output_path, 'w', encoding='utf-8') as f:
                        f.write(svg_content)
                else:
                    try:
                        img.save(self.output_path, format=pil_fmt)
                    except Exception as save_err:
                        # If Pillow save fails (e.g. JXL), encode via FFmpeg fallback from PNG buffer
                        ffmpeg_exe = get_local_ffmpeg_exe()
                        if not ffmpeg_exe:
                            raise save_err
                        temp_png = self.output_path + ".tmp.png"
                        img.save(temp_png, format='PNG')
                        cmd = [ffmpeg_exe, "-y", "-i", temp_png]
                        if target_fmt not in ['gif', 'webp']:
                            cmd.extend(["-frames:v", "1", "-update", "1"])
                        cmd.append(self.output_path)
                        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                        if os.path.exists(temp_png):
                            os.remove(temp_png)
                        if res.returncode != 0:
                            raise Exception(f"Encode failed: {res.stdout.decode('utf-8', errors='ignore')}")
            finally:
                try:
                    img.close()
                except Exception:
                    pass
            self.status = "Completed"
            self.progress = 100
        except Exception as e:
            import traceback
            print(f"[DEBUG PIL ERR] {traceback.format_exc()}")
            pillow_err = str(e)
            ffmpeg_err = ""
            
            # Prevent FFmpeg fallback for proprietary document formats
            if input_ext in ['.cdr']:
                self.status = "Failed"
                self.error_message = pillow_err
                return
                
            # Fallback to FFmpeg for direct image conversion if entire pipeline encountered an error
            try:
                ffmpeg_exe = get_local_ffmpeg_exe()
                if ffmpeg_exe:
                    cmd = [ffmpeg_exe, "-y", "-i", self.input_path]
                    if target_fmt not in ['gif', 'webp']:
                        cmd.extend(["-frames:v", "1", "-update", "1"])
                    cmd.append(self.output_path)
                    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                    if res.returncode == 0:
                        self.status = "Completed"
                        self.progress = 100
                        return
                    else:
                        ffmpeg_err = res.stdout.decode('utf-8', errors='ignore')
            except Exception as fe:
                ffmpeg_err = str(fe)
                
            self.status = "Failed"
            self.error_message = f"PIL: {pillow_err} | FFmpeg: {ffmpeg_err}"

    def _convert_media(self):
        try:
            ffmpeg_exe = get_local_ffmpeg_exe()
            if not ffmpeg_exe:
                raise Exception("FFmpeg not found.")
            settings = SettingsManager()
            hw_accel = settings.get('hw_accel', 'auto')
            if hw_accel == 'auto':
                from src.backend.gpu_detector import detect_best_gpu
                hw_accel, _, _ = detect_best_gpu()
            video_preset = settings.get('video_preset', 'medium')
            audio_bitrate = settings.get('audio_bitrate', '192k')
            default_video_codec = settings.get('default_video_codec', 'h264')
            default_audio_codec = settings.get('default_audio_codec', 'aac')

            cmd = [ffmpeg_exe, "-y"]
            
            if hw_accel == 'nvenc':
                cmd.extend(["-hwaccel", "cuda"])
            elif hw_accel == 'qsv':
                cmd.extend(["-hwaccel", "qsv"])
            # AMF typically uses d3d11va or dxva2 for decode on Windows, 
            # but it's safest to omit the decode flag or use d3d11va if we know it's Windows.
            # We'll rely solely on the encoder (h264_amf/hevc_amf) for acceleration.

            cmd.extend(["-i", self.input_path])
            
            if self.target_format in ["mp3", "wav", "flac", "m4a", "aac", "aiff", "alac", "wma", "amr", "ac3", "eac3", "thd", "dts", "ogg"]:
                ext = os.path.splitext(self.input_path)[1].lower().lstrip('.')
                has_art = False
                
                if self.target_format in ["mp3", "flac", "m4a", "aiff", "alac", "wma", "ac3", "eac3", "thd", "dts"]:
                    if ext in ['mp3', 'flac', 'm4a', 'aac', 'ogg', 'wav', 'aiff', 'alac', 'dff', 'dsf', 'mqa', 'mod', 's3m', 'xm', 'it', 'wma', 'ra', 'bwf', 'amr', 'ac3', 'eac3', 'thd', 'dts', 'dtshd', 'aob']:
                        cmd.extend(["-map", "0:a:0?", "-map", "0:v:0?", "-c:v", "copy"])
                        if self.target_format == "mp3":
                            cmd.extend(["-id3v2_version", "3"])
                        has_art = True
                    elif ext in ['mp4', 'mkv', 'avi', 'mov', 'webm', 'wmv', 'flv', 'f4v', 'mxf', 'asf', 'mts', 'm2ts', 'vob', 'ts', '3gp', '3g2', 'ogv', 'rm', 'rmvb', 'vro', 'dat', 'mpg', 'mpeg', 'm3u8', 'm3u', 'm4s']:
                        import tempfile
                        import hashlib
                        name_hash = hashlib.md5(self.input_path.encode()).hexdigest()
                        cover_temp = os.path.join(tempfile.gettempdir(), f"cover_{name_hash}.jpg")
                        
                        subprocess.run([
                            ffmpeg_exe, "-y", "-ss", "00:00:01", "-i", self.input_path, 
                            "-vframes", "1", "-q:v", "2", cover_temp
                        ], creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        
                        if not (os.path.exists(cover_temp) and os.path.getsize(cover_temp) > 0):
                            subprocess.run([
                                ffmpeg_exe, "-y", "-ss", "00:00:00", "-i", self.input_path, 
                                "-vframes", "1", "-q:v", "2", cover_temp
                            ], creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            
                        if os.path.exists(cover_temp) and os.path.getsize(cover_temp) > 0:
                            cmd.extend(["-i", cover_temp, "-map", "0:a:0?", "-map", "1:v:0", "-c:v", "copy", "-disposition:v", "attached_pic"])
                            if self.target_format == "mp3":
                                cmd.extend(["-id3v2_version", "3"])
                            self.temp_files_to_clean = getattr(self, 'temp_files_to_clean', [])
                            self.temp_files_to_clean.append(cover_temp)
                            has_art = True
                            
                if not has_art:
                    cmd.extend(["-vn"]) # no video
                    
                if self.target_format == "mp3":
                    cmd.extend(["-acodec", "libmp3lame", "-b:a", audio_bitrate])
                elif self.target_format == "wav":
                    cmd.extend(["-acodec", "pcm_s16le"])
                elif self.target_format == "flac":
                    cmd.extend(["-acodec", "flac"])
                elif self.target_format in ["m4a", "aac"]:
                    cmd.extend(["-acodec", "aac", "-b:a", audio_bitrate])
                elif self.target_format == "ogg":
                    cmd.extend(["-acodec", "libvorbis", "-b:a", audio_bitrate])
                elif self.target_format == "wma":
                    cmd.extend(["-acodec", "wmav2", "-b:a", audio_bitrate])
                elif self.target_format == "alac":
                    cmd.extend(["-acodec", "alac", "-f", "ipod"])
                elif self.target_format == "ac3":
                    cmd.extend(["-acodec", "ac3", "-b:a", audio_bitrate])
                elif self.target_format == "eac3":
                    cmd.extend(["-acodec", "eac3", "-b:a", audio_bitrate])
                elif self.target_format == "thd":
                    cmd.extend(["-acodec", "truehd", "-strict", "-2"])
                elif self.target_format == "dts":
                    cmd.extend(["-acodec", "dca", "-strict", "-2"])
                elif self.target_format == "aiff":
                    cmd.extend(["-acodec", "pcm_s16be"])
                elif self.target_format == "amr":
                    cmd.extend(["-acodec", "libopencore_amrnb", "-ar", "8000", "-ac", "1", "-b:a", "12.2k"])
                else:
                    cmd.extend(["-acodec", "copy"])
                cmd.append(self.output_path)
            else:
                # Video conversions
                vcodec = default_video_codec
                acodec = default_audio_codec
                extra_args = []
                disable_audio = False

                if self.target_format in ['m3u8', 'm3u', 'hls']:
                    # Package HLS stream and segments cleanly into dedicated subfolder
                    hls_dir = os.path.splitext(self.output_path)[0]
                    os.makedirs(hls_dir, exist_ok=True)
                    m3u8_name = os.path.basename(self.output_path)
                    target_m3u8 = os.path.join(hls_dir, m3u8_name)
                    segment_pattern = os.path.join(hls_dir, "segment_%03d.ts")
                    extra_args.extend([
                        "-f", "hls",
                        "-hls_time", "6",
                        "-hls_list_size", "0",
                        "-hls_segment_filename", segment_pattern
                    ])
                    self.output_path = target_m3u8
                elif self.target_format in ['mpd', 'dash']:
                    # Package DASH stream and chunks cleanly into dedicated subfolder
                    dash_dir = os.path.splitext(self.output_path)[0]
                    os.makedirs(dash_dir, exist_ok=True)
                    mpd_name = os.path.basename(self.output_path)
                    target_mpd = os.path.join(dash_dir, mpd_name)
                    extra_args.extend([
                        "-f", "dash",
                        "-seg_duration", "6",
                        "-use_template", "1",
                        "-use_timeline", "1"
                    ])
                    self.output_path = target_mpd
                elif self.target_format in ['m4s', 'fmp4']:
                    extra_args.extend(["-f", "mp4", "-movflags", "+frag_keyframe+empty_moov+default_base_moof"])
                elif self.target_format == 'cmfv':
                    extra_args.extend(["-f", "mp4", "-movflags", "+frag_keyframe+empty_moov+default_base_moof"])
                    disable_audio = True
                elif self.target_format == 'cmfa':
                    extra_args.extend(["-f", "mp4", "-movflags", "+frag_keyframe+empty_moov+default_base_moof", "-vn"])
                elif self.target_format in ['ismv', 'isma']:
                    extra_args.extend(["-f", "ismv"])
                    if self.target_format == 'isma':
                        extra_args.append("-vn")
                elif self.target_format == 'f4f':
                    extra_args.extend(["-f", "f4v"])
                elif self.target_format in ['rm', 'rmvb']:
                    extra_args.extend(["-f", "rm"])
                    vcodec = "rv20"
                    acodec = "ac3"
                elif self.target_format == 'webm':
                    vcodec = "libvpx-vp9"
                    acodec = "libopus"
                elif self.target_format == 'ogv':
                    vcodec = "libtheora"
                    acodec = "libvorbis"
                elif self.target_format in ['m2ts', 'mts', 'ts']:
                    acodec = "ac3"
                elif self.target_format in ['mpg', 'mpeg', 'vob', 'm2v', 'm1v']:
                    vcodec = "mpeg2video" if self.target_format != 'm1v' else "mpeg1video"
                    acodec = "ac3" if self.target_format == 'vob' else "mp2"
                elif self.target_format in ['wmv', 'asf']:
                    vcodec = "wmv2"
                    acodec = "wmav2"
                    if self.target_format == 'asf':
                        extra_args.extend(["-f", "asf"])
                elif self.target_format == 'f4v':
                    extra_args.extend(["-f", "f4v"])
                elif self.target_format == 'mxf':
                    extra_args.extend(["-f", "mxf", "-pix_fmt", "yuv422p", "-ar", "48000"])
                    vcodec = "mpeg2video"
                    acodec = "pcm_s16le"
                elif self.target_format == 'nut':
                    extra_args.extend(["-f", "nut"])
                elif self.target_format in ['h264', 'h265', 'hevc']:
                    vcodec = "libx265" if self.target_format in ['h265', 'hevc'] else "libx264"
                    disable_audio = True
                elif self.target_format == 'yuv':
                    vcodec = "rawvideo"
                    extra_args.extend(["-f", "rawvideo", "-pix_fmt", "yuv420p"])
                    disable_audio = True
                elif self.target_format in ['3gp', '3g2']:
                    extra_args.extend(["-f", self.target_format])
                input_ext = os.path.splitext(self.input_path)[1].lower().lstrip('.')
                
                # Check for incompatible copy situations
                non_mp4_audio_exts = {'asf', 'wmv', 'wma', 'rm', 'rmvb', 'ra', 'vro', 'dat', 'mpg', 'mpeg', 'm2v', 'm1v', 'ogg', 'ogv', 'flv', 'swf', 'webm', 'wav', 'aiff', 'amr'}
                if acodec == "copy" and self.target_format in ['mp4', 'm4v', 'mov', '3gp', '3g2'] and input_ext in non_mp4_audio_exts:
                    acodec = "aac"
                elif acodec == "copy" and self.target_format in ['webm']:
                    acodec = "libopus"
                elif acodec == "copy" and self.target_format in ['ogv']:
                    acodec = "libvorbis"
                elif acodec == "copy" and self.target_format in ['wmv', 'asf']:
                    acodec = "wmav2"

                non_mp4_video_exts = {'asf', 'wmv', 'rm', 'rmvb', 'flv', 'vro', 'dat', 'mpg', 'mpeg', 'm2v', 'm1v', 'webm', 'ogv', 'avi', 'mvi', 'roq'}
                if vcodec == "copy" and self.target_format in ['mp4', 'm4v', 'mov'] and input_ext in non_mp4_video_exts:
                    vcodec = "h264"
                elif vcodec == "copy" and self.target_format in ['webm']:
                    vcodec = "libvpx-vp9"
                elif vcodec == "copy" and self.target_format in ['ogv']:
                    vcodec = "libtheora"
                elif vcodec == "copy" and self.target_format in ['wmv', 'asf']:
                    vcodec = "wmv2"

                if vcodec != "copy":
                    if vcodec == "hevc":
                        if hw_accel == 'nvenc':
                            vcodec = "hevc_nvenc"
                        elif hw_accel == 'qsv':
                            vcodec = "hevc_qsv"
                        elif hw_accel == 'amf':
                            vcodec = "hevc_amf"
                        else:
                            vcodec = "libx265"
                    else:
                        if hw_accel == 'nvenc':
                            vcodec = "h264_nvenc"
                        elif hw_accel == 'qsv':
                            vcodec = "h264_qsv"
                        elif hw_accel == 'amf':
                            vcodec = "h264_amf"
                        else:
                            vcodec = "libx264"
                        
                cmd.extend(["-vcodec", vcodec])
                
                if vcodec != "copy":
                    if vcodec == "libvpx-vp9":
                        vp9_cpu_map = {"fast": "4", "medium": "2", "slow": "0"}
                        cmd.extend(["-cpu-used", vp9_cpu_map.get(video_preset, "2")])
                        cmd.extend(["-deadline", "good"])
                    elif vcodec in ["h264_amf", "hevc_amf"]:
                        amf_preset_map = {"fast": "speed", "medium": "balanced", "slow": "quality"}
                        actual_preset = amf_preset_map.get(video_preset, "balanced")
                        cmd.extend(["-preset", actual_preset])
                    elif vcodec in ["libx264", "libx265", "h264_nvenc", "hevc_nvenc", "h264_qsv", "hevc_qsv"]:
                        actual_preset = video_preset
                        cmd.extend(["-preset", actual_preset])

                if acodec == "mp3":
                    acodec = "libmp3lame"
                    
                if disable_audio:
                    cmd.append("-an")
                else:
                    cmd.extend(["-acodec", acodec])
                    if acodec not in ["copy", "pcm_s16le"]:
                        cmd.extend(["-b:a", audio_bitrate])
                    
                cmd.extend(extra_args)
                cmd.append(self.output_path)
                
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            output_lines = []
            duration = 0.0
            import re
            duration_re = re.compile(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)")
            time_re = re.compile(r"time=\s*(\d+):(\d+):(\d+\.\d+)")
            
            for line in process.stdout:
                output_lines.append(line)
                
                if duration == 0.0:
                    dur_match = duration_re.search(line)
                    if dur_match:
                        h, m, s = dur_match.groups()
                        duration = int(h) * 3600 + int(m) * 60 + float(s)
                
                if duration > 0.0:
                    time_match = time_re.search(line)
                    if time_match:
                        h, m, s = time_match.groups()
                        current_time = int(h) * 3600 + int(m) * 60 + float(s)
                        new_progress = min(99, int((current_time / duration) * 100))
                        if new_progress != getattr(self, 'progress', 0):
                            self.progress = new_progress
                            if getattr(self, 'on_update', None):
                                self.on_update()
                
            process.wait()
            
            if getattr(self, 'temp_files_to_clean', None):
                for f in self.temp_files_to_clean:
                    try:
                        if os.path.exists(f):
                            os.remove(f)
                    except Exception:
                        pass
                        
            file_ok = os.path.exists(self.output_path) and os.path.getsize(self.output_path) > 0
            has_finished_mux = any("Lsize=" in line or "muxing overhead" in line for line in output_lines)
            
            if process.returncode == 0 or (file_ok and has_finished_mux):
                self.status = "Completed"
                self.progress = 100
            else:
                # Fallback to software encoding with standard safe codecs if initial attempt failed
                safe_vcodec = "libx264"
                safe_acodec = "aac"
                fallback_extra = []
                
                if self.target_format in ['webm']:
                    safe_vcodec = "libvpx-vp9"
                    safe_acodec = "libopus"
                elif self.target_format in ['ogv']:
                    safe_vcodec = "libtheora"
                    safe_acodec = "libvorbis"
                elif self.target_format in ['wmv', 'asf']:
                    safe_vcodec = "wmv2"
                    safe_acodec = "wmav2"
                    if self.target_format == 'asf': fallback_extra.extend(["-f", "asf"])
                elif self.target_format in ['mpg', 'mpeg', 'vob', 'm2v', 'm1v']:
                    safe_vcodec = "mpeg2video" if self.target_format != 'm1v' else "mpeg1video"
                    safe_acodec = "ac3" if self.target_format == 'vob' else "mp2"
                elif self.target_format in ['avi']:
                    safe_vcodec = "mpeg4"
                    safe_acodec = "libmp3lame"
                elif self.target_format in ['flv', 'f4v']:
                    safe_vcodec = "libx264"
                    safe_acodec = "aac"
                    fallback_extra.extend(["-f", "flv"])
                elif self.target_format in ['mxf']:
                    safe_vcodec = "mpeg2video"
                    safe_acodec = "pcm_s16le"
                    fallback_extra.extend(["-f", "mxf", "-pix_fmt", "yuv422p", "-ar", "48000"])
                elif self.target_format in ['mp3']:
                    safe_acodec = "libmp3lame"
                elif self.target_format in ['wav']:
                    safe_acodec = "pcm_s16le"
                elif self.target_format in ['flac']:
                    safe_acodec = "flac"

                fallback_cmd = [ffmpeg_exe, "-y", "-i", self.input_path]
                if self.target_format not in ["mp3", "wav", "flac", "m4a", "aac", "aiff", "alac", "wma", "amr", "ac3", "eac3", "thd", "dts", "ogg"]:
                    fallback_cmd.extend(["-vcodec", safe_vcodec, "-preset", "fast"])
                    if disable_audio:
                        fallback_cmd.append("-an")
                    else:
                        fallback_cmd.extend(["-acodec", safe_acodec, "-b:a", audio_bitrate])
                else:
                    fallback_cmd.extend(["-vn", "-acodec", safe_acodec])
                    if safe_acodec not in ["copy", "pcm_s16le"]:
                        fallback_cmd.extend(["-b:a", audio_bitrate])
                fallback_cmd.extend(fallback_extra)
                fallback_cmd.append(self.output_path)

                fb_proc = subprocess.Popen(
                    fallback_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    encoding='utf-8',
                    errors='replace',
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                fb_output = []
                for line in fb_proc.stdout:
                    fb_output.append(line)
                    if duration == 0.0:
                        dur_match = duration_re.search(line)
                        if dur_match:
                            h, m, s = dur_match.groups()
                            duration = int(h) * 3600 + int(m) * 60 + float(s)
                    if duration > 0.0:
                        time_match = time_re.search(line)
                        if time_match:
                            h, m, s = time_match.groups()
                            current_time = int(h) * 3600 + int(m) * 60 + float(s)
                            new_progress = min(99, int((current_time / duration) * 100))
                            if new_progress != getattr(self, 'progress', 0):
                                self.progress = new_progress
                                if getattr(self, 'on_update', None):
                                    self.on_update()
                fb_proc.wait()
                file_ok = os.path.exists(self.output_path) and os.path.getsize(self.output_path) > 0
                has_finished_mux = any("Lsize=" in line or "muxing overhead" in line for line in fb_output)
                
                if fb_proc.returncode == 0 or (file_ok and has_finished_mux):
                    self.status = "Completed"
                    self.progress = 100
                else:
                    self.status = "Failed"
                    full_output = "".join(output_lines) + "\n--- Fallback Output ---\n" + "".join(fb_output)
                    try:
                        with open("ffmpeg_error.log", "w", encoding="utf-8") as f:
                            f.write(f"Command: {' '.join(cmd)}\nFallback: {' '.join(fallback_cmd)}\n\nOutput:\n{full_output}")
                    except Exception:
                        pass
                    tail = "".join(fb_output[-3:]).strip()
                    self.error_message = f"FFmpeg exited with code {fb_proc.returncode}: {tail}"
                
        except Exception as e:
            self.status = "Failed"
            self.error_message = str(e)

    def _convert_markup(self):
        try:
            from src.backend.pandoc_manager import get_pandoc_exe
            exe_path = get_pandoc_exe()
            if not exe_path:
                raise Exception("pandoc binary not found or could not be downloaded.")
            
            cmd = [exe_path, self.input_path, "-o", self.output_path]
            
            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if res.returncode == 0:
                self.status = "Completed"
                self.progress = 100
            else:
                self.status = "Failed"
                self.error_message = f"pandoc failed with code {res.returncode}:\n{res.stdout.strip()[-100:]}"
        except Exception as e:
            self.status = "Failed"
            self.error_message = str(e)

    def _convert_data(self):
        try:
            import json
            import csv
            import xmltodict
            import yaml
            
            ext_in = os.path.splitext(self.input_path)[1].lower()
            ext_out = f".{self.target_format.lower()}"
            
            data = None
            
            # Read input
            with open(self.input_path, 'r', encoding='utf-8') as f:
                if ext_in == '.json':
                    data = json.load(f)
                elif ext_in in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                elif ext_in in ['.csv', '.txt', '.log']:
                    # Assume TXT/LOG is CSV for data formats
                    reader = csv.DictReader(f)
                    data = list(reader)
                elif ext_in == '.xml':
                    data = xmltodict.parse(f.read())
                    # Flatten out single root if possible
                    if isinstance(data, dict) and len(data) == 1:
                        data = list(data.values())[0]
                        if isinstance(data, dict) and len(data) == 1 and isinstance(list(data.values())[0], list):
                            data = list(data.values())[0]
                elif ext_in == '.vcf':
                    data = []
                    current = {}
                    for line in f:
                        line = line.strip()
                        if line == 'BEGIN:VCARD': current = {}
                        elif line == 'END:VCARD': 
                            if current: data.append(current)
                        elif ':' in line:
                            k, v = line.split(':', 1)
                            k = k.split(';')[0].strip()
                            if k and v.strip(): current[k] = v.strip()
                elif ext_in == '.ics':
                    data = []
                    current = None
                    for line in f:
                        line = line.strip()
                        if line == 'BEGIN:VEVENT': current = {}
                        elif line == 'END:VEVENT':
                            if current is not None: data.append(current); current = None
                        elif current is not None and ':' in line:
                            k, v = line.split(':', 1)
                            k = k.split(';')[0].strip()
                            if k and v.strip(): current[k] = v.strip()
            
            if data is None:
                raise Exception(f"Unsupported input data format: {ext_in}")
                
            # Write output
            with open(self.output_path, 'w', encoding='utf-8', newline='') as f:
                if ext_out == '.json':
                    json.dump(data, f, indent=2)
                elif ext_out in ['.yaml', '.yml']:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)
                elif ext_out == '.csv':
                    if isinstance(data, dict):
                        data = [data]
                    if not isinstance(data, list) or not data:
                        raise Exception("Cannot convert to CSV: Data is not a list of items.")
                    
                    # Ensure all items are dicts and collect headers
                    headers = set()
                    for item in data:
                        if isinstance(item, dict):
                            headers.update(item.keys())
                    
                    if not headers:
                        raise Exception("Cannot convert to CSV: No structured fields found.")
                        
                    headers = sorted(list(headers), key=lambda x: str(x) if x is not None else "")
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                    for item in data:
                        if isinstance(item, dict):
                            writer.writerow(item)
                elif ext_out == '.pdf':
                    import fitz
                    import html as html_lib
                    if isinstance(data, list) and data and isinstance(data[0], dict):
                        raw_headers = list(set().union(*(item.keys() for item in data if isinstance(item, dict))))
                        headers = sorted(raw_headers, key=lambda x: str(x) if x is not None else "")
                        rows_html = "".join("<tr>" + "".join(f"<td style='border:1px solid #ddd;padding:8px;'>{html_lib.escape(str(row.get(h, '')))}</td>" for h in headers) + "</tr>" for row in data if isinstance(row, dict))
                        header_html = "".join(f"<th style='border:1px solid #ddd;padding:8px;background:#f2f4f7;text-align:left;'>{html_lib.escape(str(h))}</th>" for h in headers)
                        html_content = f"<html><body style='font-family:sans-serif;padding:16px;'><table style='border-collapse:collapse;width:100%;font-size:12px;'><thead><tr>{header_html}</tr></thead><tbody>{rows_html}</tbody></table></body></html>"
                    else:
                        pretty_str = json.dumps(data, indent=2)
                        html_content = f"<html><body style='font-family:sans-serif;padding:16px;'><pre style='font-family:monospace;background:#f8fafc;padding:14px;border:1px solid #e2e8f0;border-radius:6px;font-size:12px;'>{html_lib.escape(pretty_str)}</pre></body></html>"
                    doc = fitz.open(stream=html_content.encode('utf-8'), filetype="html")
                    pdf_bytes = doc.convert_to_pdf()
                    with open(self.output_path, 'wb') as f_out:
                        f_out.write(pdf_bytes)
                    doc.close()
                elif ext_out == '.xml':
                    import xmltodict
                    import re
                    
                    def sanitize_keys(obj):
                        if isinstance(obj, dict):
                            new_dict = {}
                            for k, v in obj.items():
                                new_k = str(k).strip() if k is not None else "item"
                                new_k = re.sub(r'[^a-zA-Z0-9_\-.]', '_', new_k)
                                if new_k and new_k[0].isdigit():
                                    new_k = '_' + new_k
                                if not new_k:
                                    new_k = "item"
                                new_dict[new_k] = sanitize_keys(v)
                            return new_dict
                        elif isinstance(obj, list):
                            return [sanitize_keys(i) for i in obj]
                        else:
                            return obj
                            
                    safe_data = sanitize_keys(data)
                    
                    if isinstance(safe_data, list):
                        xml_data = {'root': {'item': safe_data}}
                    elif isinstance(safe_data, dict):
                        if len(safe_data) == 1:
                            xml_data = safe_data
                        else:
                            xml_data = {'root': safe_data}
                    else:
                        xml_data = {'root': {'value': str(safe_data)}}
                    f.write(xmltodict.unparse(xml_data, pretty=True))
                else:
                    raise Exception(f"Unsupported target data format: {ext_out}")
            
            self.status = "Completed"
            self.progress = 100
        except Exception as e:
            self.status = "Failed"
            self.error_message = str(e)



    def _convert_pdf_to_image(self):
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(self.input_path)
            num_pages = len(doc)
            target_fmt = self.target_format.lower().strip()
            
            if num_pages == 0:
                raise Exception("PDF has no pages.")
                
            if num_pages == 1:
                # Single page: output directly to the requested output_path
                page = doc.load_page(0)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
                pix.save(self.output_path)
            else:
                # Multiple pages: create a folder named after the file
                name_no_ext = os.path.splitext(os.path.basename(self.input_path))[0]
                folder_path = os.path.join(self.output_dir, f"{name_no_ext}_images")
                os.makedirs(folder_path, exist_ok=True)
                
                for i in range(num_pages):
                    page = doc.load_page(i)
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    out_name = f"page_{i + 1}.{target_fmt}"
                    out_path = os.path.join(folder_path, out_name)
                    pix.save(out_path)
                
                # Update output path so the UI can open the folder or the first image
                self.output_path = folder_path
                
            doc.close()
            self.status = "Completed"
            self.progress = 100
        except Exception as e:
            self.status = "Failed"
            self.error_message = f"PyMuPDF failed: {str(e)}"

    def _convert_epub_to_pdf(self):
        try:
            import fitz
            doc = fitz.open(self.input_path)
            pdf_bytes = doc.convert_to_pdf()
            with open(self.output_path, 'wb') as f:
                f.write(pdf_bytes)
            doc.close()
            self.status = "Completed"
            self.progress = 100
        except Exception as e:
            self.status = "Failed"
            self.error_message = f"EPUB to PDF failed: {str(e)}"

    def _convert_ebook(self):
        try:
            target_fmt = self.target_format.lower().strip()
            image_formats = ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'tif', 'avif', 'jxl', 'heic', 'heif', 'tga', 'pcx', 'ppm']

            if target_fmt == 'epub':
                pdf_to_epub(self.input_path, self.output_path)
            else:
                doc = load_ebook_doc(self.input_path)
                if target_fmt == 'pdf':
                    pdf_bytes = doc.convert_to_pdf()
                    with open(self.output_path, 'wb') as f:
                        f.write(pdf_bytes)
                elif target_fmt in image_formats:
                    import fitz
                    num_pages = len(doc)
                    if num_pages == 0:
                        raise Exception("E-Book file has no pages.")
                        
                    def _save_pixmap(pix, out_path):
                        if target_fmt in ['png', 'jpg', 'jpeg']:
                            pix.save(out_path)
                        else:
                            from PIL import Image
                            mode = "RGBA" if pix.alpha else "RGB"
                            img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
                            if target_fmt in ['jpg', 'jpeg', 'bmp', 'pcx', 'ppm']:
                                if img.mode != 'RGB': img = img.convert('RGB')
                            elif target_fmt in ['tiff', 'tif']:
                                pfmt = 'TIFF'
                            elif target_fmt in ['heic', 'heif']:
                                pfmt = 'HEIF'
                            else:
                                pfmt = target_fmt.upper()
                            try:
                                img.save(out_path, format=pfmt if 'pfmt' in locals() else None)
                            except Exception:
                                # Fallback via temp png and ffmpeg
                                temp_png = out_path + ".tmp.png"
                                img.save(temp_png, format='PNG')
                                subprocess.run(['ffmpeg', '-y', '-i', temp_png, '-frames:v', '1', '-update', '1', out_path], check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                                if os.path.exists(temp_png): os.remove(temp_png)

                    if num_pages == 1:
                        page = doc.load_page(0)
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                        _save_pixmap(pix, self.output_path)
                    else:
                        name_no_ext = os.path.splitext(os.path.basename(self.input_path))[0]
                        folder_path = os.path.join(self.output_dir, f"{name_no_ext}_images")
                        os.makedirs(folder_path, exist_ok=True)
                        for i in range(num_pages):
                            page = doc.load_page(i)
                            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                            out_name = f"page_{i + 1}.{target_fmt}"
                            out_path = os.path.join(folder_path, out_name)
                            _save_pixmap(pix, out_path)
                        self.output_path = folder_path
                else:
                    raise Exception(f"Unsupported eBook target format: {target_fmt}")
                doc.close()
            self.status = "Completed"
            self.progress = 100
        except Exception as e:
            self.status = "Failed"
            self.error_message = f"E-Book conversion failed: {str(e)}"

    def _convert_3d(self):
        try:
            import trimesh
            import tempfile
            import shutil
            from src.backend.assimp_manager import convert_with_assimp, get_assimp_export_id
            
            ext = os.path.splitext(self.input_path)[1].lower()
            target_fmt = self.target_format.lower()
            
            # 1. Primary Engine: Assimp (Handles materials, binary FBX, and 40+ formats natively)
            assimp_id = get_assimp_export_id(target_fmt)
            if assimp_id:
                try:
                    convert_with_assimp(self.input_path, self.output_path, export_format_id=assimp_id)
                    if os.path.exists(self.output_path):
                        self.status = "Completed"
                        self.progress = 100
                        return
                except Exception as e:
                    print(f"Assimp direct conversion failed or unsupported input ({ext}): {e}. Falling back to legacy Trimesh pipeline.")
            
            # 2. Legacy Fallback Pipeline (Trimesh / FBX2glTF / OpenSCAD)
            working_input = self.input_path
            
            # If the input is FBX, we must first convert it to a temporary GLB using FBX2glTF
            if ext == '.fbx':
                from src.backend.fbx2gltf_manager import get_fbx2gltf_exe
                exe_path = get_fbx2gltf_exe()
                if not exe_path:
                    raise Exception("FBX2glTF binary not found or could not be downloaded.")
                
                # FBX2glTF outputs to a .glb by default if we specify it.
                temp_glb = os.path.join(tempfile.gettempdir(), f"temp_{os.path.basename(self.input_path)}.glb")
                
                cmd = [exe_path, "-i", self.input_path, "-o", temp_glb, "-b"] # -b for binary glb
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                
                if res.returncode != 0 or not os.path.exists(temp_glb):
                    raise Exception(f"FBX2glTF failed: {res.stderr.decode('utf-8', errors='ignore')}")
                
                # If the user only wanted a GLB, we can just move it to the output and finish
                if self.target_format.lower() in ['glb', 'gltf']:
                    import shutil
                    shutil.move(temp_glb, self.output_path)
                    self.status = "Completed"
                    self.progress = 100
                    return
                
                # Otherwise, continue with trimesh using the temp GLB
                working_input = temp_glb
                self.temp_files_to_clean = getattr(self, 'temp_files_to_clean', [])
                self.temp_files_to_clean.append(temp_glb)
                
            elif ext == '.scad':
                import shutil
                openscad_exe = shutil.which("openscad") or shutil.which("openscad.exe")
                if not openscad_exe:
                    raise Exception("OpenSCAD is required to convert .scad files. Please install OpenSCAD and ensure it is in your PATH.")
                
                temp_stl = os.path.join(tempfile.gettempdir(), f"temp_{os.path.basename(self.input_path)}.stl")
                cmd = [openscad_exe, "-o", temp_stl, self.input_path]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                if res.returncode != 0 or not os.path.exists(temp_stl):
                    raise Exception(f"OpenSCAD failed: {res.stderr.decode('utf-8', errors='ignore')}")
                
                if self.target_format.lower() == 'stl':
                    shutil.move(temp_stl, self.output_path)
                    self.status = "Completed"
                    self.progress = 100
                    return
                
                working_input = temp_stl
                self.temp_files_to_clean = getattr(self, 'temp_files_to_clean', [])
                self.temp_files_to_clean.append(temp_stl)
                
            elif ext == '.dwf':
                raise Exception("DWF parsing requires Autodesk Forge or a native DWF to DXF converter. Direct conversion is not supported natively.")
                
            elif ext == '.3ds':
                raise Exception("Assimp failed to parse this 3DS file and there is no secondary fallback available.")


            
            # Load the mesh
            if ext in ['.dxf', '.dwg']:
                mesh = parse_dxf_facets(working_input)
            elif ext in ['.step', '.stp', '.iges', '.igs']:
                mesh = parse_step_facets(working_input)
            else:
                mesh = trimesh.load(working_input, force='mesh')
            
            if self.target_format.lower() == 'fbx':
                export_mesh_to_ascii_fbx(mesh, self.output_path)
            else:
                mesh.export(self.output_path)
            
            self.status = "Completed"
            self.progress = 100
        except ImportError as e:
            self.status = "Failed"
            self.error_message = f"A required 3D library is missing: {str(e)}. (E.g., run 'pip install trimesh pycollada')"
        except Exception as e:
            self.status = "Failed"
            self.error_message = f"3D Conversion failed: {str(e)}"

    def _convert_subtitle(self):
        try:
            items = parse_subtitle(self.input_path)
            content = export_subtitle(items, self.target_format)
            with open(self.output_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.status = "Completed"
            self.progress = 100
        except Exception as e:
            self.status = "Failed"
            self.error_message = f"Subtitle conversion failed: {str(e)}"

    def _convert_font(self):
        try:
            from fontTools.ttLib import TTFont
            import subprocess
            import shutil
            
            # For OTF to TTF conversion, use otf2ttf
            target = self.target_format.lower().strip()
            ext = os.path.splitext(self.input_path)[1].lower().strip('.')
            
            # Handle EOT format conversion
            if target == 'eot':
                # EOT generally requires a TTF base
                temp_ttf = self.output_path + ".ttf"
                fontNumber = 0 if ext in ['dfont', 'ttc', 'otc'] else -1
                font = TTFont(self.input_path, fontNumber=fontNumber)
                font.flavor = None
                font.save(temp_ttf)
                font.close()
                try:
                    subprocess.run(['ttf2eot', temp_ttf, self.output_path], check=True, capture_output=True)
                    os.remove(temp_ttf)
                    self.status = "Completed"
                    self.progress = 100
                    return
                except FileNotFoundError:
                    os.remove(temp_ttf)
                    raise Exception("ttf2eot utility is missing. Please install it (e.g. npm install -g ttf2eot)")
                except subprocess.CalledProcessError as e:
                    os.remove(temp_ttf)
                    raise Exception(f"ttf2eot conversion failed: {e.stderr.decode()}")
            
            # WOFF and WOFF2 conversions
            if target in ['woff', 'woff2']:
                fontNumber = 0 if ext in ['dfont', 'ttc', 'otc'] else -1
                font = TTFont(self.input_path, fontNumber=fontNumber)
                font.flavor = target
                font.save(self.output_path)
                font.close()
                self.status = "Completed"
                self.progress = 100
                return
            
            # For converting TO TTF or OTF
            fontNumber = 0 if ext in ['dfont', 'ttc', 'otc'] else -1
            if ext == 'eot':
                temp_ttf = self.input_path + ".ttf"
                try:
                    subprocess.run(['eot2ttf', self.input_path, temp_ttf], check=True, capture_output=True)
                    font = TTFont(temp_ttf, fontNumber=-1)
                    os.remove(temp_ttf)
                except FileNotFoundError:
                    raise Exception("eot2ttf utility is missing. Please install it (e.g. npm install -g eot2ttf)")
            else:
                font = TTFont(self.input_path, fontNumber=fontNumber)
            is_cff = 'CFF ' in font or font.sfntVersion == 'OTTO'
            font.close()
            
            if target in ['ttf', 'otf']:
                if target == 'ttf' and is_cff:
                    # If CFF outlines, try otf2ttf for outline conversion if installed, otherwise save directly
                    try:
                        subprocess.run(['otf2ttf', self.input_path, '-o', self.output_path, '--overwrite'], check=True, capture_output=True)
                    except (FileNotFoundError, subprocess.CalledProcessError):
                        font = TTFont(self.input_path, fontNumber=fontNumber)
                        font.flavor = None
                        font.save(self.output_path)
                        font.close()
                else:
                    font = TTFont(self.input_path, fontNumber=fontNumber)
                    font.flavor = None
                    font.save(self.output_path)
                    font.close()

            self.status = "Completed"
            self.progress = 100
        except Exception as e:
            self.status = "Failed"
            self.error_message = f"Font conversion failed: {str(e)}"

    def _convert_database(self):
        try:
            data = parse_database(self.input_path)
            export_database(data, self.target_format, self.output_path)
            self.status = "Completed"
            self.progress = 100
        except Exception as e:
            self.status = "Failed"
            self.error_message = f"Database conversion failed: {str(e)}"

    def _convert_gis(self):
        try:
            geojson_data = parse_gis(self.input_path)
            export_gis(geojson_data, self.target_format, self.output_path)
            self.status = "Completed"
            self.progress = 100
        except Exception as e:
            self.status = "Failed"
            self.error_message = f"GIS conversion failed: {str(e)}"

    def _convert_archive(self):
        import tempfile
        import shutil
        target = self.target_format.lower().strip()
        name_no_ext = os.path.splitext(os.path.basename(self.input_path))[0]
        
        if target in ['folder', 'extract']:
            folder_path = os.path.join(self.output_dir, f"{name_no_ext}_extracted")
            os.makedirs(folder_path, exist_ok=True)
            try:
                unpack_archive(self.input_path, folder_path)
                self.output_path = folder_path
                self.status = "Completed"
                self.progress = 100
            except Exception as e:
                self.status = "Failed"
                self.error_message = f"Archive extraction failed: {str(e)}"
        else:
            temp_dir = tempfile.mkdtemp()
            try:
                unpack_archive(self.input_path, temp_dir)
                pack_archive(temp_dir, self.output_path, self.target_format)
                self.status = "Completed"
                self.progress = 100
            except Exception as e:
                self.status = "Failed"
                self.error_message = f"Archive conversion failed: {str(e)}"
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _convert_document(self):
        ext = os.path.splitext(self.input_path)[1].lower()
        office2pdf_supported = ['.docx', '.xlsx', '.pptx']
        win32_err = ""
        
        # Check for Apple iWork formats (Keynote, Pages, Numbers) which contain embedded PDFs
        if ext in ['.key', '.pages', '.numbers']:
            try:
                import zipfile
                with zipfile.ZipFile(self.input_path, 'r') as z:
                    if 'QuickLook/Preview.pdf' in z.namelist():
                        with z.open('QuickLook/Preview.pdf') as source, open(self.output_path, "wb") as target:
                            target.write(source.read())
                        self.status = "Completed"
                        self.progress = 100
                        return
                    else:
                        raise Exception(f"No embedded PDF preview found in {ext} file. Please save it with 'Include Preview' enabled in Apple iWork.")
            except zipfile.BadZipFile:
                pass # Not a standard modern iWork zip, fallback to failure
            except Exception as e:
                self.status = "Failed"
                self.error_message = f"Apple iWork extraction failed: {str(e)}"
                return

        # Tier 1: Try win32com (Microsoft Office)
        try:
            import win32com.client
            import pythoncom
            
            # Initialize COM for background threads
            pythoncom.CoInitialize()
            
            abs_in = os.path.abspath(self.input_path)
            abs_out = os.path.abspath(self.output_path)
            
            if ext in ['.doc', '.docx', '.docm', '.dot', '.dotx', '.dotm', '.rtf', '.txt', '.odt', '.mht', '.html', '.htm', '.xml', '.wpd', '.wps']:
                word = win32com.client.Dispatch("Word.Application")
                try:
                    doc = word.Documents.Open(abs_in)
                    doc.SaveAs(abs_out, FileFormat=17) # wdFormatPDF
                    doc.Close()
                finally:
                    word.Quit()
                    
            elif ext in ['.xls', '.xlsx', '.xlsm', '.xlsb', '.csv', '.ods', '.sxc']:
                excel = win32com.client.Dispatch("Excel.Application")
                try:
                    wb = excel.Workbooks.Open(abs_in)
                    wb.ExportAsFixedFormat(0, abs_out) # xlTypePDF
                    wb.Close(False)
                finally:
                    excel.Quit()
                    
            elif ext in ['.ppt', '.pptx', '.pptm', '.pps', '.odp']:
                ppt = win32com.client.Dispatch("PowerPoint.Application")
                try:
                    presentation = ppt.Presentations.Open(abs_in, WithWindow=False)
                    presentation.SaveAs(abs_out, 32) # ppSaveAsPDF
                    presentation.Close()
                finally:
                    ppt.Quit()
                    
            elif ext in ['.vsd', '.vsdx']:
                visio = win32com.client.Dispatch("Visio.Application")
                visio.Visible = False
                try:
                    doc = visio.Documents.Open(abs_in)
                    doc.ExportAsFixedFormat(1, abs_out, 1, 0) # visFixedFormatPDF
                    doc.Close()
                finally:
                    visio.Quit()
                    
            elif ext == '.pub':
                pub = win32com.client.Dispatch("Publisher.Application")
                try:
                    doc = pub.Open(abs_in)
                    doc.ExportAsFixedFormat(2, abs_out) # pbFixedFormatTypePDF
                    doc.Close()
                finally:
                    pub.Quit()
                    
            elif ext == '.mpp':
                project = win32com.client.Dispatch("MSProject.Application")
                project.Visible = False
                try:
                    project.FileOpen(abs_in)
                    project.DocumentExport(abs_out, 2) # pjPDF
                    project.FileClose(0) # pjDoNotSave
                finally:
                    project.Quit()
            
            if os.path.exists(self.output_path):
                self.status = "Completed"
                self.progress = 100
                return
            
        except ImportError:
            win32_err = "pywin32 not installed."
        except Exception as e:
            win32_err = str(e)
        finally:
            try:
                import pythoncom
                pythoncom.CoUninitialize()
            except:
                pass
                
        # Tier 2: Try LibreOffice (headless) fallback
        try:
            import shutil
            soffice_exe = shutil.which("soffice") or shutil.which("soffice.exe") or shutil.which("libreoffice")
            if not soffice_exe and os.name == 'nt':
                for default_path in [
                    r"C:\Program Files\LibreOffice\program\soffice.exe",
                    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
                ]:
                    if os.path.exists(default_path):
                        soffice_exe = default_path
                        break
            if soffice_exe:
                cmd = [soffice_exe, "--headless", "--convert-to", "pdf", "--outdir", self.output_dir, self.input_path]
                res = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    encoding='utf-8',
                    errors='replace',
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                if res.returncode == 0 and os.path.exists(self.output_path):
                    self.status = "Completed"
                    self.progress = 100
                    return
        except Exception:
            pass

        # Tier 3: Try WPS Office (COM Automation) fallback
        try:
            import win32com.client
            import pythoncom
            pythoncom.CoInitialize()
            abs_in = os.path.abspath(self.input_path)
            abs_out = os.path.abspath(self.output_path)
            wps_success = False

            if ext in ['.doc', '.docx', '.docm', '.dot', '.dotx', '.dotm', '.rtf', '.txt', '.odt', '.mht', '.html', '.htm', '.xml', '.wpd', '.wps']:
                for prog_id in ["Kwps.Application", "Wps.Application"]:
                    try:
                        wps = win32com.client.Dispatch(prog_id)
                        doc = wps.Documents.Open(abs_in)
                        doc.ExportAsFixedFormat(abs_out, 17) # 17 = wdFormatPDF
                        doc.Close()
                        wps.Quit()
                        wps_success = True
                        break
                    except Exception:
                        pass
            elif ext in ['.xls', '.xlsx', '.xlsm', '.xlsb', '.csv', '.ods', '.sxc']:
                for prog_id in ["Ket.Application", "Et.Application"]:
                    try:
                        et = win32com.client.Dispatch(prog_id)
                        wb = et.Workbooks.Open(abs_in)
                        wb.ExportAsFixedFormat(0, abs_out) # 0 = xlTypePDF
                        wb.Close(False)
                        et.Quit()
                        wps_success = True
                        break
                    except Exception:
                        pass
            elif ext in ['.ppt', '.pptx', '.pptm', '.pps', '.odp']:
                for prog_id in ["Kwpp.Application", "Wpp.Application"]:
                    try:
                        wpp = win32com.client.Dispatch(prog_id)
                        presentation = wpp.Presentations.Open(abs_in, WithWindow=False)
                        presentation.SaveAs(abs_out, 32) # 32 = ppSaveAsPDF
                        presentation.Close()
                        wpp.Quit()
                        wps_success = True
                        break
                    except Exception:
                        pass

            if wps_success and os.path.exists(self.output_path):
                self.status = "Completed"
                self.progress = 100
                return
        except Exception:
            pass
        finally:
            try:
                import pythoncom
                pythoncom.CoUninitialize()
            except Exception:
                pass

        # Tier 4: Try office2pdf fallback (modern formats only)
        if ext in office2pdf_supported:
            try:
                from src.backend.office2pdf_manager import get_office2pdf_exe
                exe_path = get_office2pdf_exe()
                if exe_path:
                    cmd = [exe_path, self.input_path, "-o", self.output_path]
                    res = subprocess.run(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        encoding='utf-8',
                        errors='replace',
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    )
                    if res.returncode == 0:
                        self.status = "Completed"
                        self.progress = 100
                        return
            except Exception:
                pass

        self.status = "Failed"
        self.error_message = f"Failed to convert format '{ext}'. Microsoft Office, LibreOffice, or WPS Office is required. (Error: {win32_err})"

    def _convert_vector(self):
        try:
            ext = os.path.splitext(self.input_path)[1].lower()
            target_fmt = self.target_format.lower().strip()
            image_formats = ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'ico']

            if ext == '.cdr':
                # 1. Try LibreOffice CLI (libcdr)
                try:
                    import shutil
                    soffice_exe = shutil.which("soffice") or shutil.which("soffice.exe") or shutil.which("libreoffice")
                    if not soffice_exe and os.name == 'nt':
                        for default_path in [
                            r"C:\Program Files\LibreOffice\program\soffice.exe",
                            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
                        ]:
                            if os.path.exists(default_path):
                                soffice_exe = default_path
                                break
                    if soffice_exe:
                        cmd = [soffice_exe, "--headless", "--convert-to", target_fmt, "--outdir", self.output_dir, self.input_path]
                        res = subprocess.run(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            encoding='utf-8',
                            errors='replace',
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                        )
                        if res.returncode == 0 and os.path.exists(self.output_path):
                            self.status = "Completed"
                            self.progress = 100
                            return
                except Exception:
                    pass

                # 2. Try Inkscape CLI
                try:
                    import shutil
                    inkscape_exe = shutil.which("inkscape") or shutil.which("inkscape.exe")
                    if not inkscape_exe and os.name == 'nt':
                        for default_path in [
                            r"C:\Program Files\Inkscape\bin\inkscape.exe",
                            r"C:\Program Files\Inkscape\inkscape.exe"
                        ]:
                            if os.path.exists(default_path):
                                inkscape_exe = default_path
                                break
                    if inkscape_exe:
                        cmd = [inkscape_exe, self.input_path, f"--export-filename={self.output_path}"]
                        res = subprocess.run(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            encoding='utf-8',
                            errors='replace',
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                        )
                        if res.returncode == 0 and os.path.exists(self.output_path):
                            self.status = "Completed"
                            self.progress = 100
                            return
                except Exception:
                    pass

                # 3. Fallback: Extract embedded preview image
                img = open_cdr_preview(self.input_path)
                if target_fmt in image_formats:
                    if target_fmt in ['jpg', 'jpeg', 'bmp']:
                        img = img.convert('RGB')
                    elif target_fmt == 'png':
                        img = img.convert('RGBA') if img.mode not in ('RGB', 'RGBA') else img
                    elif target_fmt == 'ico':
                        img.save(self.output_path, format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
                        self.status = "Completed"
                        self.progress = 100
                        return
                    img.save(self.output_path)
                elif target_fmt == 'pdf':
                    img.convert('RGB').save(self.output_path, format='PDF')
                elif target_fmt == 'svg':
                    import base64
                    import io
                    buf = io.BytesIO()
                    img.save(buf, format='PNG')
                    b64_str = base64.b64encode(buf.getvalue()).decode('ascii')
                    w, h = img.size
                    svg_content = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><image width="{w}" height="{h}" href="data:image/png;base64,{b64_str}"/></svg>'
                    with open(self.output_path, 'w', encoding='utf-8') as f:
                        f.write(svg_content)
                else:
                    img.save(self.output_path)

                self.status = "Completed"
                self.progress = 100
                return

            import fitz  # PyMuPDF
            target_fmt = self.target_format.lower().strip()
            image_formats = ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'ico', 'tiff', 'tif', 'avif', 'jxl', 'heic', 'heif', 'tga', 'pcx', 'ppm']

            doc = fitz.open(self.input_path)

            if len(doc) == 0:
                raise Exception("Vector file has no content.")

            page = doc.load_page(0)

            if target_fmt in image_formats:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                if target_fmt in ['png', 'jpg', 'jpeg']:
                    pix.save(self.output_path)
                elif target_fmt == 'ico':
                    img_data = pix.tobytes("png")
                    from PIL import Image
                    import io
                    img = Image.open(io.BytesIO(img_data)).convert('RGBA')
                    img.save(self.output_path, format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
                else:
                    from PIL import Image
                    mode = "RGBA" if pix.alpha else "RGB"
                    img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
                    if target_fmt in ['jpg', 'jpeg', 'bmp', 'pcx', 'ppm']:
                        if img.mode != 'RGB': img = img.convert('RGB')
                    elif target_fmt in ['tiff', 'tif']:
                        pfmt = 'TIFF'
                    elif target_fmt in ['heic', 'heif']:
                        pfmt = 'HEIF'
                    else:
                        pfmt = target_fmt.upper()
                    try:
                        img.save(self.output_path, format=pfmt if 'pfmt' in locals() else None)
                    except Exception:
                        temp_png = self.output_path + ".tmp.png"
                        img.save(temp_png, format='PNG')
                        subprocess.run(['ffmpeg', '-y', '-i', temp_png, '-frames:v', '1', '-update', '1', self.output_path], check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                        if os.path.exists(temp_png): os.remove(temp_png)
            elif target_fmt == 'pdf':
                pdf_bytes = doc.convert_to_pdf()
                with open(self.output_path, 'wb') as f:
                    f.write(pdf_bytes)
            elif target_fmt == 'svg':
                svg_text = page.get_svg_image()
                with open(self.output_path, 'w', encoding='utf-8') as f:
                    f.write(svg_text)
            elif target_fmt == 'eps':
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = pix.tobytes("png")
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(img_data)).convert('RGB')
                img.save(self.output_path, format='EPS')
            else:
                raise Exception(f"Unsupported target vector format: {target_fmt}")

            doc.close()
            self.status = "Completed"
            self.progress = 100
        except Exception as e:
            self.status = "Failed"
            self.error_message = f"Vector conversion failed: {str(e)}"

    def _simulate_progress(self):
        import time
        import random
        while getattr(self, 'status', '') == "Converting" and getattr(self, 'progress', 0) < 95:
            time.sleep(0.1)
            if self.status != "Converting":
                break
            self.progress += random.randint(1, 3)
            if self.progress > 95:
                self.progress = 95
            if getattr(self, 'on_update', None):
                self.on_update()

    def run(self, on_update=None, existing_claimed_paths=None):
        self.status = "Converting"
        self.on_update = on_update
        if self.on_update: self.on_update()
        
        # Refresh output_dir from settings in case it changed since the job was queued
        if not getattr(self, '_explicit_output_dir', False):
            from src.backend.settings import SettingsManager
            settings_dir = SettingsManager().get('output_dir')
            if settings_dir:
                self.output_dir = settings_dir
            else:
                self.output_dir = os.path.dirname(self.input_path)
            
        # Re-resolve unique output_path right before conversion, checking if same name exists on disk
        name_no_ext, src_ext = os.path.splitext(os.path.basename(self.input_path))
        self.output_path = resolve_unique_path(
            self.output_dir,
            name_no_ext,
            self.target_format,
            src_ext=src_ext,
            existing_claimed_paths=existing_claimed_paths,
            input_path=self.input_path
        )
        os.makedirs(self.output_dir, exist_ok=True)
        
        ext = os.path.splitext(self.input_path)[1].lower()
        image_formats = ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif', '.heic', '.heif', '.ico', '.tiff', '.tif', '.avif', '.jxl', '.psd', '.raw', '.cr2', '.nef', '.arw', '.dng', '.raf', '.pef', '.tga', '.pcx', '.ppm', '.pgm', '.pbm', '.pnm', '.icns', '.sgi', '.dds', '.dib', '.xbm', '.xpm', '.cur', '.exr', '.dpx', '.eps', '.ps', '.cdr']
        vector_formats = ['.svg', '.ai', '.cdr', '.xps', '.oxps']
        data_formats = ['.json', '.csv', '.xml', '.yaml', '.yml', '.vcf', '.ics']
        markup_formats = ['.md', '.html', '.htm', '.rtf', '.txt', '.log']
        doc_formats = [
            '.doc', '.docx', '.docm', '.dot', '.dotx', '.dotm', '.rtf', '.txt', '.log', '.odt', '.mht', '.html', '.htm', '.xml', '.wpd', '.wps',
            '.xls', '.xlsx', '.xlsm', '.xlsb', '.csv', '.ods', '.sxc',
            '.ppt', '.pptx', '.pptm', '.pps', '.odp',
            '.key', '.pages', '.numbers',
            '.vsd', '.vsdx', '.pub', '.mpp'
        ]
        
        ebook_formats = ['.pdf', '.epub', '.mobi', '.azw3', '.azw', '.iba', '.djvu', '.djv', '.cbr', '.cbz', '.cb7', '.cbt', '.chm', '.snb', '.pdb', '.lrf', '.fb2', '.fbz']
        model3d_formats = [
            '.obj', '.stl', '.ply', '.glb', '.gltf', '.off', '.dae', '.fbx', 
            '.step', '.stp', '.iges', '.igs', '.dxf', '.dwg', '.3mf', '.scad', '.dwf', '.3ds',
            '.blend', '.x', '.lwo', '.lws', '.md5mesh', '.smd', '.vta', '.ogex', '.3d', '.b3d',
            '.q3d', '.q3s', '.nff', '.ter', '.mdl', '.xml', '.ifc', '.x3d', '.x3db', '.csm',
            '.bvh', '.ase', '.cob', '.scn', '.ac', '.ms3d', '.mqo', '.ndo', '.irr', '.irrmesh', '.pmx'
        ]
        subtitle_formats = ['.srt', '.vtt', '.ass', '.ssa', '.sub', '.scc']
        font_formats = ['.ttf', '.otf', '.woff', '.woff2', '.eot', '.dfont']
        database_formats = ['.sql', '.db', '.sqlite', '.sqlite3', '.mdb', '.accdb']
        gis_formats = ['.geojson', '.kml', '.kmz', '.gpx', '.shp']
        archive_formats = ['.zip', '.rar', '.7z', '.tar', '.gz', '.tgz', '.bz2', '.tbz2', '.xz', '.txz', '.iso', '.img', '.cab']
        
        safe_print(f"[CONVERT] input: {self.input_path}")
        safe_print(f"[CONVERT] target_format: {self.target_format}")
        safe_print(f"[CONVERT] output_path: {self.output_path}")
        
        target = f".{self.target_format.lower()}"
        
        is_media = True
        if (ext in data_formats or ext in ['.txt', '.log']) and (target in data_formats or target == '.pdf'):
            is_media = False
        elif target in markup_formats and (ext in markup_formats):
            is_media = False
        elif ext in doc_formats and self.target_format == 'pdf':
            is_media = False
        elif ext in ebook_formats and (target in image_formats or target in ['.pdf', '.epub']):
            is_media = False
        elif ext in vector_formats or target in vector_formats:
            is_media = False
        elif target in model3d_formats and ext in model3d_formats:
            is_media = False
        elif ext in subtitle_formats or target in subtitle_formats:
            is_media = False
        elif ext in font_formats and target in font_formats:
            is_media = False
        elif ext in database_formats or target in database_formats:
            is_media = False
        elif ext in gis_formats or target in gis_formats:
            is_media = False
        elif ext in archive_formats or target in archive_formats or target in ['.folder', '.extract']:
            is_media = False
        elif ext in image_formats and target in image_formats:
            is_media = False
            
        if not is_media:
            threading.Thread(target=self._simulate_progress, daemon=True).start()
        
        if (ext in data_formats or ext in ['.txt', '.log']) and (target in data_formats or target == '.pdf'):
            self._convert_data()
        elif target in markup_formats and (ext in markup_formats):
            self._convert_markup()
        elif ext in doc_formats and self.target_format == 'pdf':
            self._convert_document()
        elif ext in ebook_formats and (target in image_formats or target in ['.pdf', '.epub']):
            self._convert_ebook()
        elif ext in vector_formats or target in vector_formats:
            self._convert_vector()
        elif target in model3d_formats and ext in model3d_formats:
            self._convert_3d()
        elif ext in subtitle_formats or target in subtitle_formats:
            self._convert_subtitle()
        elif ext in font_formats and target in font_formats:
            self._convert_font()
        elif ext in database_formats or target in database_formats:
            self._convert_database()
        elif ext in gis_formats or target in gis_formats:
            self._convert_gis()
        elif ext in archive_formats or target in archive_formats or target in ['.folder', '.extract']:
            self._convert_archive()
        elif ext in image_formats and target in image_formats:
            self._convert_image()
        else:
            self._convert_media()
            
        safe_print(f"[CONVERT] status after run: {self.status}, error: {self.error_message}")
        if self.status == "Completed":
            self.progress = 100
        if on_update: on_update()

class ConverterManager:
    def __init__(self):
        self.jobs = []
        
    def add_job(self, input_path, target_format):
        claimed = [
            j.output_path for j in self.jobs 
            if hasattr(j, 'output_path') and j.output_path and getattr(j, 'status', 'Pending') in ('Pending', 'Converting')
        ]
        job = ConversionJob(input_path, target_format, existing_claimed_paths=claimed)
        self.jobs.append(job)
        return job

    def remove_job(self, job):
        if job in self.jobs:
            self.jobs.remove(job)

    def clear_jobs(self):
        self.jobs.clear()
        
    def run_job_async(self, job, on_update=None):
        def _run():
            job.run(on_update)
        threading.Thread(target=_run, daemon=True).start()
