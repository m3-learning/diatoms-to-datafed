import json
import numpy as np


# JSON Encoder for numpy types and complex numbers
class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        # Handle numpy integer types
        if isinstance(obj, np.integer):
            return int(obj)
        # Handle numpy floating-point types
        elif isinstance(obj, np.floating):
            return float(obj)
        # Handle numpy arrays
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        # Handle bytes by decoding them to UTF-8 strings
        elif isinstance(obj, bytes):
            return obj.decode("utf-8")
        # Handle complex numbers by returning a list of [real, imaginary]
        elif isinstance(obj, complex):
            return [obj.real, obj.imag]
        # Fallback to the default JSON encoding for other types
        else:
            return super(MyEncoder, self).default(obj)


# Base Class
class MetaXtractor:
    """
    Base class for extracting metadata from different file formats.
    Subclasses must implement the extract() method.
    """
    def __init__(self, file_name):
        """
        Constructor that initializes the extractor with the file name.
        :param file_name: Name of the file from which metadata will be extracted.
        """
        self.file_name = file_name

    def extract(self):
        """
        Placeholder method for extracting metadata, to be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method")
