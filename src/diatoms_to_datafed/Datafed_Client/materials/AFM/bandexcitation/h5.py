import h5py
from MetaXtract import MetaXtractor


class H5(MetaXtractor):
    """
    Class for extracting metadata from HDF5 (.h5) files.
    """

    def extract(self):
        def extract_h5_data(name, obj):
            # Only include attributes where the length of the value is <= 10
            attrs = {k: v for k, v in obj.attrs.items() if len(str(v)) <= 10}
            return {name: attrs}

        with h5py.File(self.file_name, 'r') as f:
            metadata = {}
            # Visit all items in the HDF5 file and collect metadata
            f.visititems(lambda name, obj: metadata.update(extract_h5_data(name, obj)))
        return metadata
