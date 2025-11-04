# plugins/forward_copy.py
# Forward as Copy - Batch, Pause, Resume, Stop
# Ultroid Userbot (Telethon) - GUNAKAN client (bukan asst)
# Aman meski asst tidak bisa masuk grup

"""
✘ Commands Available -

• - **v0.0.1.1.0 [Mod by @AlphaXproject team]**  

Forward as Copy - Batch Copy Messages (Tanpa "Forwarded from")

Perintah:
  .fcopy <sumber> <tujuan> <maks_pesan> <pesan_per_batch>
        → Mulai copy pesan sebagai pesan asli (tanpa tag forward)

  .fcopystatus → Cek progress copy
  .fcopystop   → Hentikan proses copy secara permanen
  .fcopypause  → Jeda sementara proses copy
  .fcopyresume → Lanjutkan proses yang dijeda

Contoh:
  .fcopy -1001234567890 -1000987654321 500 30
        → Copy 500 pesan dari grup A ke grup B, 30 pesan per batch

Catatan:
  • Gunakan ID chat (contoh: -1001234567890)
  • Userbot HARUS berada di grup sumber & tujuan
  • Copy sebagai pesan asli (bukan forward)
  • Progress tersimpan otomatis (tahan restart)
  • Aman dari FloodWait (jeda 6 detik per batch)
"""

# Ekstrak versi menggunakan regex
import re
# Ekstrak versi dari string dokumentasi anonim
# [MODIFIED] Perbarui pola regex untuk mencocokkan versi baru (v0.1.11.2) agar lebih fleksibel
version_match = re.search(r"v\d+\.\d+\.\d+\.\d+ \[\w+ by @\w+ team\]", __doc__, re.MULTILINE)
PLUGIN_VERSION = version_match.group(0) if version_match else "Unknown"

# Debug: Log saat plugin dimuat
import os
print(f"DEBUG: mengimport module/addons - {os.path.basename(__file__)} {PLUGIN_VERSION}")  # MODIFIED: Use __file__ to dynamically get the current file name


from telethon import functions
from telethon.errors import FloodWaitError
from .. import ultroid_cmd, eor, udB, client, LOG_CHANNEL
import asyncio

# === KEY UDB ===
KEY_ACTIVE = "FCOPY_ACTIVE"
KEY_PAUSED = "FCOPY_PAUSED"
KEY_SRC = "FCOPY_SRC"
KEY_DST = "FCOPY_DST"
KEY_MAX = "FCOPY_MAX"
KEY_BATCH = "FCOPY_BATCH"
KEY_OFFSET = "FCOPY_OFFSET"
KEY_TOTAL = "FCOPY_TOTAL"

# === FUNGSI UTAMA ===
async def fcopy_worker():
    src = udB.get_key(KEY_SRC)
    dst = udB.get_key(KEY_DST)
    max_msg = udB.get_key(KEY_MAX)
    batch = udB.get_key(KEY_BATCH)
    offset = udB.get_key(KEY_OFFSET) or 0
    total = udB.get_key(KEY_TOTAL) or 0

    try:
        src_ent = await client.get_entity(src)
        dst_ent = await client.get_entity(dst)
        src_name = src_ent.title if hasattr(src_ent, "title") else str(src)
        dst_name = dst_ent.title if hasattr(dst_ent, "title") else str(dst)
    except Exception as e:
        await client.send_message(LOG_CHANNEL, f"<b>FCOPY ERROR:</b> Gagal akses grup\n<code>{e}</code>", parse_mode="html")
        udB.del_key(KEY_ACTIVE)
        return

    await client.send_message(LOG_CHANNEL,
        f"<b>FCOPY START</b>\n"
        f"From: <b>{src_name}</b>\n"
        f"To: <b>{dst_name}</b>\n"
        f"Max: <code>{max_msg}</code> | Batch: <code>{batch}</code>",
        parse_mode="html"
    )

    while udB.get_key(KEY_ACTIVE) and total < max_msg:
        if udB.get_key(KEY_PAUSED):
            await asyncio.sleep(5)
            continue

        try:
            result = await client(functions.messages.GetMessagesRequest(
                channel=src_ent,
                id=list(range(offset, offset + batch))
            ))
            msgs = [m for m in result.messages if m and not getattr(m, 'empty', False)]
            if not msgs:
                break

            success = 0
            for msg in msgs:
                if total >= max_msg:
                    break
                try:
                    await client.copy_message(dst, src, msg.id)
                    success += 1
                    total += 1
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    print(f"Skip {msg.id}: {e}")

            last_id = max(m.id for m in msgs)
            offset = last_id + 1
            udB.set_key(KEY_OFFSET, offset)
            udB.set_key(KEY_TOTAL, total)

            await client.send_message(LOG_CHANNEL,
                f"<b>Batch:</b> <code>{success}</code> | "
                f"Total: <code>{total}/{max_msg}</code> | "
                f"Next ID: <code>{offset}</code>",
                parse_mode="html"
            )
            await asyncio.sleep(6)  # jeda antar batch

        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)
        except Exception as e:
            await client.send_message(LOG_CHANNEL, f"<b>ERROR:</b> {e}", parse_mode="html")
            break

    # Selesai
    udB.del_key(KEY_ACTIVE)
    udB.del_key(KEY_PAUSED)
    await client.send_message(LOG_CHANNEL,
        f"<b>FCOPY SELESAI</b>\n"
        f"Total: <code>{total}</code> pesan\n"
        f"Offset: <code>{offset}</code>",
        parse_mode="html"
    )

# === .fcopy ===
@ultroid_cmd(pattern="fcopy( (.*)|$)")
async def start_fcopy(e):
    if udB.get_key(KEY_ACTIVE):
        return await eor(e, "`Proses copy sudah berjalan!`")

    args = e.pattern_match.group(1).strip()
    if not args:
        return await eor(e, "Gunakan:\n`.fcopy <src> <dst> <max> <batch>`\nContoh: `.fcopy -100123 -100456 500 30`")

    try:
        src, dst, max_msg, batch = args.split()[:4]
        src = int(src)
        dst = int(dst)
        max_msg = int(max_msg)
        batch = int(batch)
        if batch < 1 or batch > 100: raise ValueError
        if max_msg < 1: raise ValueError
    except:
        return await eor(e, "Format salah! Gunakan ID chat.\nContoh: `.fcopy -1001234567890 -1000987654321 1000 30`")

    # Simpan config
    udB.set_key(KEY_SRC, src)
    udB.set_key(KEY_DST, dst)
    udB.set_key(KEY_MAX, max_msg)
    udB.set_key(KEY_BATCH, batch)
    udB.set_key(KEY_OFFSET, 0)
    udB.set_key(KEY_TOTAL, 0)
    udB.set_key(KEY_ACTIVE, True)
    udB.del_key(KEY_PAUSED)

    # Jalankan worker
    client.copy_task = asyncio.create_task(fcopy_worker())

    await eor(e, f"**FCOPY Dimulai**\n"
                 f"Sumber: `{src}`\n"
                 f"Tujuan: `{dst}`\n"
                 f"Maks: `{max_msg}` | Batch: `{batch}`\n"
                 f"Gunakan `.fcopystatus`")

# === .fcopystatus ===
@ultroid_cmd(pattern="fcopystatus")
async def status(e):
    if not udB.get_key(KEY_ACTIVE):
        return await eor(e, "`Tidak ada proses copy aktif.`")

    total = udB.get_key(KEY_TOTAL) or 0
    offset = udB.get_key(KEY_OFFSET) or 0
    max_msg = udB.get_key(KEY_MAX)
    paused = "PAUSED" if udB.get_key(KEY_PAUSED) else "RUNNING"

    await eor(e, f"**FCOPY STATUS**\n"
                 f"Status: `{paused}`\n"
                 f"Progress: `{total}/{max_msg}`\n"
                 f"Next ID: `{offset}`")

# === .fcopystop ===
@ultroid_cmd(pattern="fcopystop")
async def stop(e):
    if not udB.get_key(KEY_ACTIVE):
        return await eor(e, "`Tidak ada proses aktif.`")

    udB.del_key(KEY_ACTIVE)
    udB.del_key(KEY_PAUSED)
    if hasattr(client, "copy_task") and client.copy_task:
        client.copy_task.cancel()

    await eor(e, f"**FCOPY Dihentikan**\n"
                 f"Total: `{udB.get_key(KEY_TOTAL) or 0}`\n"
                 f"Offset: `{udB.get_key(KEY_OFFSET) or 0}`")

# === .fcopypause ===
@ultroid_cmd(pattern="fcopypause")
async def pause(e):
    if not udB.get_key(KEY_ACTIVE):
        return await eor(e, "`Tidak ada proses aktif.`")
    if udB.get_key(KEY_PAUSED):
        return await eor(e, "`Sudah dalam pause.`")

    udB.set_key(KEY_PAUSED, True)
    await eor(e, "`FCOPY Dijeda. Gunakan .fcopyresume untuk lanjut.`")

# === .fcopyresume ===
@ultroid_cmd(pattern="fcopyresume")
async def resume(e):
    if not udB.get_key(KEY_ACTIVE):
        return await eor(e, "`Tidak ada proses aktif.`")
    if not udB.get_key(KEY_PAUSED):
        return await eor(e, "`Tidak dalam pause.`")

    udB.del_key(KEY_PAUSED)
    await eor(e, "`FCOPY Dilanjutkan.`")


msg_log = f"DEBUG: module/addons - {os.path.basename(__file__)} loaded successfully {PLUGIN_VERSION}"
LOGS.info(msg_log)
print(msg_log)
