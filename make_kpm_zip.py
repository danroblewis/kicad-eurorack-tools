import os
from zipfile import ZipFile

# Create object of ZipFile
with ZipFile('kpm-eurorack-tools.zip', 'w') as zip_object:
    # Traverse all files in directory
    for folder_name, sub_folders, file_names in os.walk('library'):
        for filename in file_names:
               file_path = os.path.join(folder_name, filename)
               print(file_path)
               zip_object.write(file_path, file_path.replace("library/",""))

print("done")
