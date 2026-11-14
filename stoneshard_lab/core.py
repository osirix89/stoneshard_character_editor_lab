"""Stoneshard Character Lab - save parsing, checksums and experimental edits.

This tool is unofficial. It only works on files selected by the user and never
writes into the game's save directory unless the user explicitly chooses it.
"""
from __future__ import annotations
import copy, hashlib, json, re, zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SAVE_SALT_PREFIX = "stOne!characters_v1!"
SAVE_SALT_SUFFIX = "!shArd"

class SaveFormatError(Exception):
    pass

@dataclass
class DecodedFile:
    path: Path
    data: dict[str, Any]
    json_text: str
    checksum: str
    checksum_valid: bool | None
    compressed_size: int
    raw_size: int


def compact_json(obj: Any) -> str:
    # Match JavaScript JSON.stringify formatting: UTF-8, no spaces, non-ASCII kept.
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def decode_compressed_json_bytes(blob: bytes, path: Path, kind: str, character_folder: str,
                                 save_folder: str | None = None) -> DecodedFile:
    """Decode a save blob and verify its path-dependent MD5 suffix."""
    try:
        raw = zlib.decompress(blob)
    except zlib.error as exc:
        raise SaveFormatError(f"No se pudo descomprimir {path.name}: {exc}") from exc
    if len(raw) < 33 or raw[-1:] != b"\x00":
        raise SaveFormatError("No se encontró el sufijo MD5 + byte NUL esperado.")
    try:
        stored = raw[-33:-1].decode("ascii", errors="strict").lower()
    except UnicodeDecodeError as exc:
        raise SaveFormatError("El sufijo MD5 no es ASCII.") from exc
    if not re.fullmatch(r"[0-9a-f]{32}", stored):
        raise SaveFormatError("El sufijo final no parece ser un MD5 hexadecimal.")
    json_bytes = raw[:-33]
    try:
        json_text = json_bytes.decode("utf-8")
        parsed = json.loads(json_text)
    except Exception as exc:
        raise SaveFormatError(f"El JSON interno no es válido: {exc}") from exc
    if not isinstance(parsed, dict):
        raise SaveFormatError("La raíz del JSON no es un objeto.")
    if kind == "sav":
        if not save_folder:
            raise SaveFormatError("Falta el nombre de carpeta autosave_N/exitsave_N/save_N.")
        salt = f"{SAVE_SALT_PREFIX}{character_folder}!{save_folder}{SAVE_SALT_SUFFIX}"
    elif kind == "character_map":
        salt = f"{SAVE_SALT_PREFIX}{character_folder}{SAVE_SALT_SUFFIX}"
    elif kind == "save_map":
        if not save_folder:
            raise SaveFormatError("Falta el nombre de carpeta de guardado.")
        salt = f"{SAVE_SALT_PREFIX}{character_folder}!{save_folder}{SAVE_SALT_SUFFIX}"
    else:
        raise ValueError(kind)
    expected = hashlib.md5((json_text + salt).encode("utf-8")).hexdigest()
    return DecodedFile(path, parsed, json_text, stored, stored == expected, len(blob), len(raw))


def decode_compressed_json(path: Path, kind: str, character_folder: str,
                           save_folder: str | None = None) -> DecodedFile:
    return decode_compressed_json_bytes(path.read_bytes(), path, kind, character_folder, save_folder)


def encode_compressed_json(obj: dict, kind: str, character_folder: str,
                           save_folder: str | None = None) -> bytes:
    json_text = compact_json(obj)
    if kind == "sav":
        if not save_folder: raise ValueError("save_folder requerido")
        salt = f"{SAVE_SALT_PREFIX}{character_folder}!{save_folder}{SAVE_SALT_SUFFIX}"
    elif kind == "character_map":
        salt = f"{SAVE_SALT_PREFIX}{character_folder}{SAVE_SALT_SUFFIX}"
    elif kind == "save_map":
        if not save_folder: raise ValueError("save_folder requerido")
        salt = f"{SAVE_SALT_PREFIX}{character_folder}!{save_folder}{SAVE_SALT_SUFFIX}"
    else:
        raise ValueError(kind)
    md5 = hashlib.md5((json_text + salt).encode("utf-8")).hexdigest()
    return zlib.compress((json_text + md5 + "\x00").encode("utf-8"), level=6)


def skill_records(root: dict) -> list[dict]:
    arr = root.get("skillsDataMap", {}).get("skillsAllDataList", [])
    records = []
    if not isinstance(arr, list): return records
    for i in range(0, len(arr) - 4, 5):
        if arr[i] is None: continue
        records.append({"id": str(arr[i]), "learned": arr[i+1] is True or arr[i+1] == 1,
                        "learned_index": i+1, "block": copy.deepcopy(arr[i:i+5]), "offset": i})
    return records


def set_skill(root: dict, skill_id: str, learned: bool) -> bool:
    arr = root.get("skillsDataMap", {}).get("skillsAllDataList", [])
    for i in range(0, len(arr)-4, 5):
        if str(arr[i]) == skill_id:
            arr[i+1] = bool(learned)
            return True
    return False


def find_paths(obj: Any, target: str, prefix="$", out=None):
    if out is None: out=[]
    if isinstance(obj, dict):
        for k,v in obj.items():
            p=f"{prefix}.{k}"
            if k == target: out.append((p,v))
            find_paths(v,target,p,out)
    elif isinstance(obj,list):
        for i,v in enumerate(obj): find_paths(v,target,f"{prefix}[{i}]",out)
    return out


def get_path(obj: Any, path: str):
    cur=obj
    for part in path.split("."):
        if not part: continue
        m=re.fullmatch(r"([^\[]+)(?:\[(\d+)\])?",part)
        if not m: raise ValueError(f"Ruta no válida: {part}")
        key,idx=m.groups()
        if isinstance(cur,dict): cur=cur[key]
        else: raise KeyError(key)
        if idx is not None: cur=cur[int(idx)]
    return cur


def set_path(obj: Any, path: str, value: Any):
    parts=path.split("."); cur=obj
    for part in parts[:-1]:
        m=re.fullmatch(r"([^\[]+)(?:\[(\d+)\])?",part)
        if not m: raise ValueError(f"Ruta no válida: {part}")
        key,idx=m.groups(); cur=cur[key]
        if idx is not None: cur=cur[int(idx)]
    m=re.fullmatch(r"([^\[]+)(?:\[(\d+)\])?",parts[-1])
    if not m: raise ValueError("Ruta final no válida")
    key,idx=m.groups()
    if idx is None: cur[key]=value
    else: cur[key][int(idx)]=value
