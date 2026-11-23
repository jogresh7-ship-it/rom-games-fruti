#!/usr/bin/env python3
"""Turn big PSP games, and every PS2 game, uploaded as .7z / .zip (whole or in parts) into .cso parts.

PS2: the PS2 player reads the disc while playing and can't look inside archives, so any zipped
PS2 game is converted (to .iso parts when the .cso would be over 2 GB, the CSO format's limit).

Browsers can't unpack PSP games bigger than about 1 GB (they run out of memory), but the PSP
emulator reads .cso (a compressed ISO) directly, without unpacking. This runs on GitHub Actions:
for each folder in rom/PSP/ whose game is an archive holding an .iso over the size limit,
it unpacks the archive, compresses the .iso to .cso, writes the .cso in 25 MB parts named
"<folder name>.part001.cso", ... and removes the archive parts. Other files (cover, ...) stay.

Usage: psp_to_cso.py <repo root>    Prints the folders it converted, one per line, on stdout.
"""
import os, re, sys, glob, struct, zlib, shutil, subprocess, tempfile
from multiprocessing import Pool

LIMIT = 1024 * 1024 * 1024          # convert when the unpacked .iso is bigger than this
PART = 25 * 1024 * 1024             # size of each .cso part (the GitHub website's upload limit)
BS = 2048                           # CSO block size
SKIP = re.compile(r'(^\.)|\.(md|txt|nfo|sfv|url|py|js|json|html|css|jpe?g|png|webp|gif)$|^[^.]+$', re.I)


def joined_name(name):
    """Same rule as library.js: the file name without its part number."""
    name = re.sub(r'\.\d{1,3}$', '', name)
    name = re.sub(r'\.part\d+$', '', name, flags=re.I)
    return re.sub(r'[\s._-]*[([]?part[\s._-]*\d+[)\]]?(?=\.[a-z0-9]+$)', '', name, flags=re.I)


def natural(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]


def game_files(folder):
    """The biggest set of files that belong together (one file or its parts), like library.js."""
    sets = {}
    for f in os.listdir(folder):
        p = os.path.join(folder, f)
        if not os.path.isfile(p) or SKIP.search(f):
            continue
        sets.setdefault(joined_name(f).lower(), []).append(p)
    if not sets:
        return []
    best = max(sets.values(), key=lambda fs: sum(os.path.getsize(x) for x in fs))
    return sorted(best, key=lambda p: natural(os.path.basename(p)))


def archive_kind(path):
    with open(path, 'rb') as f:
        b = f.read(6)
    if b == b"7z\xbc\xaf'\x1c":
        return '7z'
    if b[:4] == b'PK\x03\x04':
        return 'zip'
    return None


def listed_iso(archive):
    """(name, size) of the biggest .iso / .cso in the archive, from `7z l -slt`."""
    out = subprocess.run(['7z', 'l', '-slt', archive], capture_output=True, text=True).stdout
    best, cur = None, {}
    for line in out.splitlines() + ['']:
        if not line.strip():
            if cur.get('Path', '').lower().endswith(('.iso', '.cso')) and cur.get('Size', '').isdigit():
                if not best or int(cur['Size']) > best[1]:
                    best = (cur['Path'], int(cur['Size']))
            cur = {}
        elif ' = ' in line:
            k, v = line.split(' = ', 1)
            cur[k] = v
    return best


def comp(chunk):
    out = []
    for i in range(0, len(chunk), BS):
        b = chunk[i:i + BS]
        c = zlib.compressobj(9, zlib.DEFLATED, -15)
        d = c.compress(b) + c.flush()
        out.append(d if len(d) < len(b) else None)
    return chunk, out


class TooBig(Exception):
    pass


def iso_to_cso(src, dst):
    size = os.path.getsize(src)
    n = (size + BS - 1) // BS
    idx, pos = [], 24 + 4 * (n + 1)
    with open(src, 'rb') as f, open(dst, 'wb') as o, Pool(os.cpu_count() or 2) as pool:
        o.write(b'CISO' + struct.pack('<IQIBBH', 24, size, BS, 1, 0, 0))
        o.write(b'\0' * 4 * (n + 1))
        for chunk, blocks in pool.imap(comp, iter(lambda: f.read(BS * 4096), b''), chunksize=1):
            for i, d in enumerate(blocks):
                if d is None:
                    raw = chunk[i * BS:(i + 1) * BS]
                    idx.append(pos | 0x80000000); o.write(raw); pos += len(raw)
                else:
                    idx.append(pos); o.write(d); pos += len(d)
        idx.append(pos)
        if pos >= 0x80000000:
            raise TooBig(src)
        o.seek(24)
        o.write(struct.pack('<%dI' % len(idx), *idx))


def verify_cso(cso, iso):
    """Unpack the .cso again and compare with the .iso, block by block."""
    with open(cso, 'rb') as c, open(iso, 'rb') as i:
        total, bs = struct.unpack('<QI', c.read(24)[8:20])
        n = (total + bs - 1) // bs
        idx = struct.unpack('<%dI' % (n + 1), c.read(4 * (n + 1)))
        for k in range(n):
            a, b = idx[k] & 0x7fffffff, idx[k + 1] & 0x7fffffff
            c.seek(a); data = c.read(b - a)
            if not idx[k] & 0x80000000:
                data = zlib.decompress(data, -15)
            if data != i.read(len(data)):
                raise SystemExit('CSO check failed at block %d: %s' % (k, cso))


def split(path, folder, base, ext):
    k = 0
    with open(path, 'rb') as f:
        while True:
            b = f.read(PART)
            if not b:
                break
            k += 1
            with open(os.path.join(folder, '%s.part%03d.%s' % (base, k, ext)), 'wb') as o:
                o.write(b)
    return k


def convert(folder, limit, iso_ok):
    files = game_files(folder)
    if not files or files[0].lower().endswith('.cso'):
        return False
    kind = archive_kind(files[0])
    if not kind:
        return False
    work = tempfile.mkdtemp(dir=os.environ.get('RUNNER_TEMP'))
    try:
        archive = os.path.join(work, 'game.' + kind)
        with open(archive, 'wb') as out:
            for p in files:
                with open(p, 'rb') as f:
                    shutil.copyfileobj(f, out, 16 * 1024 * 1024)
        iso = listed_iso(archive)
        if not iso or iso[1] <= limit or not iso[0].lower().endswith('.iso'):
            return False
        print('::group::Converting %s (%s, %d MB unpacked)' % (folder, os.path.basename(iso[0]), iso[1] >> 20), file=sys.stderr)
        subprocess.run(['7z', 'e', '-y', '-o' + work, archive, iso[0]], check=True, stdout=subprocess.DEVNULL)
        os.remove(archive)
        iso_path = os.path.join(work, os.path.basename(iso[0]))
        cso = os.path.join(work, 'game.cso')
        base = os.path.basename(os.path.normpath(folder))
        try:
            iso_to_cso(iso_path, cso)
            verify_cso(cso, iso_path)
            os.remove(iso_path)
            for p in files:
                os.remove(p)
            k = split(cso, folder, base, 'cso')
            print('  -> %d .cso parts' % k, file=sys.stderr)
        except TooBig:
            if not iso_ok:
                raise SystemExit('CSO would be over 2 GB: ' + folder)
            for p in files:
                os.remove(p)
            k = split(iso_path, folder, base, 'iso')
            print('  -> %d .iso parts (too big for .cso)' % k, file=sys.stderr)
        print('::endgroup::', file=sys.stderr)
        return True
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    only = os.environ.get('ONLY_GAME', '').strip().strip('/')
    # PSP: only games too big to unpack in a browser. PS2: every zipped game.
    for console, limit, iso_ok in (('PSP', LIMIT, False), ('PS2', 0, True)):
        for folder in sorted(glob.glob(os.path.join(root, 'rom', console, '*', ''))):
            if only and os.path.basename(os.path.normpath(folder)) != only:
                continue
            if convert(folder, limit, iso_ok):
                print(os.path.relpath(folder, root).rstrip('/'))
