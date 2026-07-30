import os
import subprocess
import threading
from PIL import Image
from src.backend.ffmpeg_manager import get_local_ffmpeg_exe
from src.backend.settings import SettingsManager

try:
    import importlib
    _pillow_heif = importlib.import_module('pillow_heif')
    _pillow_heif.register_heif_opener()
except Exception:
    pass

def open_indesign_preview(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    import io
    from PIL import Image

    if ext == '.indd':
        import re
        with open(file_path, 'rb') as f:
            data = f.read()
        jpeg_starts = [m.start() for m in re.finditer(b'\xFF\xD8\xFF', data)]
        if not jpeg_starts:
            raise Exception("No embedded JPEG preview found in INDD file.")
        best_jpeg = None
        max_size = 0
        for start in jpeg_starts:
            end = data.find(b'\xFF\xD9', start)
            if end != -1:
                jpeg_data = data[start:end+2]
                if len(jpeg_data) > max_size:
                    max_size = len(jpeg_data)
                    best_jpeg = jpeg_data
        if best_jpeg and max_size > 1024:
            return Image.open(io.BytesIO(best_jpeg))
        else:
            raise Exception("Could not find a valid embedded preview image in INDD file.")
    elif ext == '.idml':
        import zipfile
        with zipfile.ZipFile(file_path, 'r') as z:
            candidates = [name for name in z.namelist() if 'thumbnail' in name.lower() or name.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if candidates:
                best_cand = max(candidates, key=lambda c: z.getinfo(c).file_size)
                img_data = z.read(best_cand)
                return Image.open(io.BytesIO(img_data))
        raise Exception("No embedded preview image found in IDML container.")
    raise Exception(f"Unsupported InDesign format: {ext}")

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
        res = subprocess.run(['hh.exe', '-decompile', temp_dir, file_path], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        
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
    elif ext in ['.mobi', '.azw3', '.azw']:
        html_str = unpack_mobi_azw3(input_path)
        return fitz.open(stream=html_str.encode('utf-8'), filetype="html")
    elif ext == '.iba':
        html_str = unpack_iba(input_path)
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
    else:
        raise Exception(f"Unsupported target archive format: {target_fmt}")

class ConversionJob:
    def __init__(self, input_path, target_format, output_dir=None):
        self.input_path = input_path
        self.target_format = target_format.lower()
        
        settings = SettingsManager()
        self.output_dir = output_dir or settings.get('output_dir') or os.path.dirname(input_path)
        
        filename = os.path.basename(input_path)
        name, _ = os.path.splitext(filename)
        self.output_path = os.path.join(self.output_dir, f"{name}.{self.target_format}")
        
        self.status = "Pending"
        self.progress = 0
        self.error_message = None

    def _convert_image(self):
        try:
            name_no_ext = os.path.splitext(os.path.basename(self.input_path))[0]
            self.output_path = os.path.join(self.output_dir, f"{name_no_ext}.{self.target_format.lower().strip()}")
            target_fmt = self.target_format.lower().strip()
            
            os.makedirs(self.output_dir, exist_ok=True)
            input_ext = os.path.splitext(self.input_path)[1].lower()
            if input_ext in ['.indd', '.idml']:
                img = open_indesign_preview(self.input_path)
            elif input_ext in ['.eps', '.ps']:
                img = open_eps_preview(self.input_path)
            elif input_ext == '.cdr':
                img = open_cdr_preview(self.input_path)
            else:
                img = Image.open(self.input_path)
            
            try:
                # Handle alpha channel & mode conversions appropriately
                if target_fmt in ['jpg', 'jpeg', 'bmp']:
                    # JPEG and BMP do not support alpha transparency or paletted modes directly
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        bg = Image.new('RGB', img.size, (255, 255, 255))
                        rgba = img.convert('RGBA')
                        bg.paste(rgba, mask=rgba.split()[3])
                        img = bg
                    else:
                        img = img.convert('RGB')
                elif target_fmt == 'png':
                    if img.mode not in ('RGB', 'RGBA', 'L', '1', 'P'):
                        img = img.convert('RGBA')
                elif target_fmt == 'webp':
                    if img.mode not in ('RGB', 'RGBA'):
                        img = img.convert('RGBA' if 'transparency' in img.info or img.mode in ('RGBA', 'LA') else 'RGB')
                elif target_fmt == 'gif':
                    if img.mode not in ('P', 'L'):
                        img = img.convert('P')
                elif target_fmt in ['heic', 'heif']:
                    img = img.convert('RGB')

                # Pillow uses 'jpeg' as the format name for jpg files
                if target_fmt == 'jpg':
                    pil_fmt = 'jpeg'
                elif target_fmt in ['heic', 'heif']:
                    pil_fmt = 'HEIF'
                elif target_fmt == 'ico':
                    pil_fmt = 'ICO'
                else:
                    pil_fmt = target_fmt
                
                if target_fmt == 'ico':
                    img.save(self.output_path, format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
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
                    img.save(self.output_path, format=pil_fmt)
            finally:
                try:
                    img.close()
                except Exception:
                    pass
            self.status = "Completed"
            self.progress = 100
        except Exception as e:
            pillow_err = str(e)
            ffmpeg_err = ""
            # Fallback to FFmpeg for image conversion if Pillow fails (e.g. animated GIFs, special encodings)
            try:
                ffmpeg_exe = get_local_ffmpeg_exe()
                if ffmpeg_exe:
                    cmd = [ffmpeg_exe, "-y", "-i", self.input_path, self.output_path]
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
            
            if self.target_format in ["mp3", "wav", "flac", "m4a", "aac", "aiff", "alac", "wma", "amr", "ac3", "eac3", "thd", "dts"]:
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
                else:
                    cmd.extend(["-acodec", "copy"])
                cmd.append(self.output_path)
            else:
                # Video conversions
                vcodec = default_video_codec
                if self.target_format == 'webm':
                    vcodec = "libvpx-vp9"
                elif vcodec != "copy":
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
                    elif hw_accel == 'amf':
                        amf_preset_map = {"fast": "speed", "medium": "balanced", "slow": "quality"}
                        actual_preset = amf_preset_map.get(video_preset, "balanced")
                        cmd.extend(["-preset", actual_preset])
                    else:
                        actual_preset = video_preset
                        cmd.extend(["-preset", actual_preset])

                acodec = default_audio_codec
                if self.target_format == 'webm':
                    acodec = "libopus"
                elif acodec == "mp3":
                    acodec = "libmp3lame"
                    
                cmd.extend(["-acodec", acodec])
                if acodec != "copy":
                    cmd.extend(["-b:a", audio_bitrate])
                    
                cmd.append(self.output_path)
                
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            
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
                        
            if process.returncode == 0:
                self.status = "Completed"
                self.progress = 100
            else:
                self.status = "Failed"
                full_output = "".join(output_lines)
                try:
                    with open("ffmpeg_error.log", "w", encoding="utf-8") as f:
                        f.write(f"Command: {' '.join(cmd)}\n\nOutput:\n{full_output}")
                except Exception:
                    pass
                # Get last 3 lines of output for the error message
                tail = "".join(output_lines[-3:]).strip()
                self.error_message = f"FFmpeg exited with code {process.returncode}: {tail}"
                
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
            
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            
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
                        
                    headers = sorted(list(headers))
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                    for item in data:
                        if isinstance(item, dict):
                            writer.writerow(item)
                elif ext_out == '.pdf':
                    import fitz
                    import html as html_lib
                    if isinstance(data, list) and data and isinstance(data[0], dict):
                        headers = sorted(list(set().union(*(item.keys() for item in data if isinstance(item, dict)))))
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
            doc = load_ebook_doc(self.input_path)
            target_fmt = self.target_format.lower().strip()
            image_formats = ['png', 'jpg', 'jpeg', 'webp', 'bmp']

            if target_fmt == 'pdf':
                pdf_bytes = doc.convert_to_pdf()
                with open(self.output_path, 'wb') as f:
                    f.write(pdf_bytes)
            elif target_fmt in image_formats:
                import fitz
                num_pages = len(doc)
                if num_pages == 0:
                    raise Exception("E-Book file has no pages.")
                if num_pages == 1:
                    page = doc.load_page(0)
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    if target_fmt in ['webp', 'bmp']:
                        from PIL import Image
                        mode = "RGBA" if pix.alpha else "RGB"
                        img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
                        img.save(self.output_path)
                    else:
                        pix.save(self.output_path)
                else:
                    name_no_ext = os.path.splitext(os.path.basename(self.input_path))[0]
                    folder_path = os.path.join(self.output_dir, f"{name_no_ext}_images")
                    os.makedirs(folder_path, exist_ok=True)
                    for i in range(num_pages):
                        page = doc.load_page(i)
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                        out_name = f"page_{i + 1}.{target_fmt}"
                        out_path = os.path.join(folder_path, out_name)
                        if target_fmt in ['webp', 'bmp']:
                            from PIL import Image
                            mode = "RGBA" if pix.alpha else "RGB"
                            img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
                            img.save(out_path)
                        else:
                            pix.save(out_path)
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
            
            if target == 'ttf':
                if is_cff:
                    # Needs outline conversion (CFF -> TrueType)
                    try:
                        subprocess.run(['otf2ttf', self.input_path, '-o', self.output_path, '--overwrite'], check=True, capture_output=True)
                    except FileNotFoundError:
                        raise Exception("otf2ttf module is missing. Please run: pip install otf2ttf")
                    except subprocess.CalledProcessError as e:
                        raise Exception(f"otf2ttf conversion failed: {e.stderr.decode()}")
                else:
                    # Already TrueType outlines (e.g. from TTF, WOFF, WOFF2)
                    font = TTFont(self.input_path)
                    font.flavor = None
                    font.save(self.output_path)
                    font.close()
            
            elif target == 'otf':
                if not is_cff:
                    # Needs TrueType -> CFF conversion which is not supported in fontTools easily
                    raise Exception("Conversion from TrueType (TTF) to OpenType (CFF/OTF) outlines is not natively supported.")
                else:
                    # Already CFF outlines (e.g. from OTF, WOFF, WOFF2)
                    font = TTFont(self.input_path)
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
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
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
                    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
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
                        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
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
                        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
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
            image_formats = ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'ico']

            doc = fitz.open(self.input_path)

            if len(doc) == 0:
                raise Exception("Vector file has no content.")

            page = doc.load_page(0)

            if target_fmt in image_formats:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                if target_fmt == 'ico':
                    img_data = pix.tobytes("png")
                    from PIL import Image
                    import io
                    img = Image.open(io.BytesIO(img_data)).convert('RGBA')
                    img.save(self.output_path, format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
                else:
                    pix.save(self.output_path)
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

    def run(self, on_update=None):
        self.status = "Converting"
        self.on_update = on_update
        if self.on_update: self.on_update()
        
        # Always rebuild output_path from the current target_format (dropdown may have changed it)
        name_no_ext = os.path.splitext(os.path.basename(self.input_path))[0]
        self.output_path = os.path.join(self.output_dir, f"{name_no_ext}.{self.target_format.lower()}")
        os.makedirs(self.output_dir, exist_ok=True)
        
        ext = os.path.splitext(self.input_path)[1].lower()
        image_formats = ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif', '.heic', '.heif', '.psd', '.ico', '.indd', '.idml', '.eps', '.ps', '.cdr', '.tga', '.pcx', '.pbm', '.pgm', '.ppm', '.exr', '.dpx', '.raf', '.pef']
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
        
        ebook_formats = ['.pdf', '.epub', '.mobi', '.azw3', '.azw', '.iba', '.djvu', '.djv', '.cbr', '.cbz', '.cb7', '.cbt', '.chm']
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
        
        print(f"[CONVERT] input: {self.input_path}")
        print(f"[CONVERT] target_format: {self.target_format}")
        print(f"[CONVERT] output_path: {self.output_path}")
        
        target = f".{self.target_format.lower()}"
        
        is_media = True
        if (ext in data_formats or ext in ['.txt', '.log']) and (target in data_formats or target == '.pdf'):
            is_media = False
        elif target in markup_formats and (ext in markup_formats):
            is_media = False
        elif ext in doc_formats and self.target_format == 'pdf':
            is_media = False
        elif ext in ebook_formats and (target in image_formats or target == '.pdf'):
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
        elif ext in ebook_formats and (target in image_formats or target == '.pdf'):
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
            
        print(f"[CONVERT] status after run: {self.status}, error: {self.error_message}")
        if self.status == "Completed":
            self.progress = 100
        if on_update: on_update()

class ConverterManager:
    def __init__(self):
        self.jobs = []
        
    def add_job(self, input_path, target_format):
        job = ConversionJob(input_path, target_format)
        self.jobs.append(job)
        return job
        
    def run_job_async(self, job, on_update=None):
        def _run():
            job.run(on_update)
        threading.Thread(target=_run, daemon=True).start()
