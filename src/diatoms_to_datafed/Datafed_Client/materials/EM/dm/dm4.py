from MetaXtract import MetaXtractor
import hyperspy.api as hs


# Subclass for DigitalMicrograph (.dm4) files
class DM4(MetaXtractor):
    """
    Class for extracting metadata from DigitalMicrograph (.dm4) files.
    """

    def extract(self):
        s = hs.load(self.file_name)  # Load the .dm4 file using HyperSpy
        metadata = s.metadata.as_dictionary()  # Extract metadata as a dictionary
        # Filter out metadata entries with value lengths > 10
        # filtered_metadata = {k: v for k, v in metadata.items() if len(str(v)) <= 10}
        return metadata
