from materials.AFM.bandexcitation.h5 import H5
from materials.AFM.oxfordAFM.ibw import IBW
from materials.EM.dm.dm4 import DM4
from materials.Xray.panalytical.xrdml import XRDML
import os
import json
import datetime


def get_file_metadata(file_path):
    """
    Extract metadata from a file based on its extension.
    For unsupported file types, return basic file information.
    """
    extension = os.path.splitext(file_path)[1].lower()
    
    print(f"Processing file with extension: {extension}")
    
    try:
        # Specific file type handlers
        if extension == '.h5':
            return H5(file_path).extract()
        elif extension == '.xrdml':
            return XRDML(file_path).extract()
        elif extension == '.dm4':
            return DM4(file_path).extract()
        elif extension == '.ibw':
            return IBW(file_path).extract()
        elif extension == '.json':
            # For JSON files, read the content directly
            with open(file_path, 'r') as f:
                return json.load(f)
        else:
            # For unsupported file types, return basic file information
            file_stat = os.stat(file_path)
            return {
                "filename": os.path.basename(file_path),
                "filesize": file_stat.st_size,
                "modified_time": datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                "created_time": datetime.datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                "file_type": extension,
                "unsupported_type": True
            }
    except Exception as e:
        # If extraction fails, still return basic info with error
        file_stat = os.stat(file_path)
        return {
            "filename": os.path.basename(file_path),
            "filesize": file_stat.st_size,
            "modified_time": datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            "created_time": datetime.datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
            "file_type": extension,
            "error": str(e)
        }