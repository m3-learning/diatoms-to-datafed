import xml.etree.ElementTree as ET
from MetaXtract import MetaXtractor


# Subclass for XRDML (.xrdml) files
class XRDML(MetaXtractor):
    """
    Class for extracting metadata from XRDML (.xrdml) files.
    """

    def extract(self):
        tree = ET.parse(self.file_name)
        root = tree.getroot()

        # Extract metadata from XML elements, skipping those with value length > 10
        metadata = {}
        for elem in root.iter():
            if elem.text and len(elem.text) <= 10:
                metadata[elem.tag] = elem.text
        return metadata
