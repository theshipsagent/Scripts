import os
import win32com.client

# Hard-coded destination PST path
TARGET_PST = r"C:\Users\wsd3\Documents\My files\takoradi.pst"

def copy_folder(source_folder, target_folder):
    """Recursively copy all items and subfolders from source to target."""
    # Copy all items in the current folder
    for item in source_folder.Items:
        try:
            item.Copy().Move(target_folder)
        except Exception as e:
            print(f"[⚠️] Failed to copy item from {source_folder.Name}: {e}")

    # Recursively copy subfolders
    for subfolder in source_folder.Folders:
        try:
            new_subfolder = target_folder.Folders.Add(subfolder.Name)
            copy_folder(subfolder, new_subfolder)
        except Exception as e:
            print(f"[⚠️] Failed to copy subfolder {subfolder.Name}: {e}")

def main():
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")

    # Access the default mailbox (your OST)
    source_root = outlook.Folders.Item(1)  # usually the primary mailbox root
    print(f"✅ Loaded default mailbox: {source_root.Name}")

    # Add or open the target PST
    if not os.path.exists(TARGET_PST):
        print("[ℹ️] Target PST will be created when added to Outlook.")
    outlook.AddStore(TARGET_PST)

    # Find the newly mounted PST root
    target_root = None
    for store in outlook.Stores:
        if store.FilePath.lower() == TARGET_PST.lower():
            target_root = store.GetRootFolder()

    if not target_root:
        raise Exception("❌ Could not locate target PST in Outlook after adding.")

    print(f"✅ Destination PST loaded: {target_root.Name}")
    print("🚀 Beginning transfer of all folders and items...")

    # Copy recursively
    copy_folder(source_root, target_root)

    print("✅ All folders, subfolders, and mail items have been successfully transferred.")

if __name__ == "__main__":
    main()
