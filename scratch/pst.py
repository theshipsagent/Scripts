import win32com.client

# === CONFIG ===
SOURCE_MAILBOX = "wsd3@outlook.com"   # Your OST mailbox name
DEST_PST = "takoradi"                 # Your target PST display name
# ==============

outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
source_root = outlook.Folders[SOURCE_MAILBOX]
dest_root = outlook.Folders[DEST_PST]

def get_or_create_folder(parent, name):
    """Get or create a subfolder safely."""
    try:
        return parent.Folders[name]
    except Exception:
        return parent.Folders.Add(name)

def migrate_folder(src_folder, dest_folder):
    """Move messages and recurse into subfolders safely."""
    folder_path = src_folder.FolderPath
    print(f"📁 Processing folder: {folder_path}")

    # --- Move messages ---
    try:
        messages = src_folder.Items
        total = messages.Count
        moved = 0
        for i in range(total, 0, -1):
            try:
                msg = messages[i]
                msg.Move(dest_folder)
                moved += 1
            except Exception as e:
                print(f"⚠️ Could not move a message in {folder_path}: {e}")
        print(f"   ✅ Moved {moved} messages from {folder_path}")
    except Exception as e:
        print(f"⚠️ Could not access messages in {folder_path}: {e}")

    # --- Recurse into subfolders ---
    try:
        for sub_src in src_folder.Folders:   # ← ✅ safe enumeration
            name = sub_src.Name.lower()
            if name in ["personmetadata", "externalcontacts", "conversation history"]:
                print(f"   ⏩ Skipping special folder: {sub_src.Name}")
                continue
            sub_dest = get_or_create_folder(dest_folder, sub_src.Name)
            migrate_folder(sub_src, sub_dest)
    except Exception as e:
        print(f"⚠️ Could not enumerate subfolders in {folder_path}: {e}")

print("🚀 Starting full mailbox migration...")

# ✅ SAFE enumeration of top-level folders
for src_folder in source_root.Folders:
    name = src_folder.Name.lower()
    if name in ["conversation history", "personmetadata", "externalcontacts"]:
        print(f"⏩ Skipping top-level special folder: {src_folder.Name}")
        continue
    dest_folder = get_or_create_folder(dest_root, src_folder.Name)
    migrate_folder(src_folder, dest_folder)

print("✅ Migration complete! All mail has been moved into the PST with folder structure preserved.")
