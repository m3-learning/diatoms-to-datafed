from igor2 import binarywave
from MetaXtract import MetaXtractor
import numpy as np
# Subclass for Igor Binary Wave (.ibw) files
class IBW(MetaXtractor):
    """
    Class for extracting metadata from Igor Binary Wave (.ibw) files.
    """
    def _read_parms(self, wave):
        """
        Helper function to extract parameters from the wave data in an .ibw file, skipping values > 10 characters.
        :param wave: The wave data extracted from the .ibw file.
        :return: A dictionary containing the metadata.
        """
        parm_dict = {}
        parm_string = wave['note']
        # Decode the byte-string if necessary
        if isinstance(parm_string, bytes):
            try:
                parm_string = parm_string.decode("utf-8")
            except UnicodeDecodeError:
                parm_string = parm_string.decode("ISO-8859-1")  # Fallback for older encoding

        parm_string = parm_string.rstrip("\r").replace(".", "_")
        parm_list = parm_string.split("\r")

        for pair_string in parm_list:
            temp = pair_string.split(":")
            if len(temp) == 2:
                temp = [item.strip() for item in temp]
                try:
                    num = float(temp[1])
                    # Skip the value if it is infinity or too long
                    if np.isinf(num):
                        continue
                    if len(str(num)) <= 10:
                        parm_dict[temp[0]] = int(num) if num == int(num) else num
                except ValueError:
                    if len(temp[1]) <= 10:
                        parm_dict[temp[0]] = temp[1]
        return parm_dict

    def extract(self):
        """
        Extract metadata from an .ibw file by reading wave data and processing parameters.
        """
        with open(self.file_name, "rb") as f:
            ibw_obj = binarywave.load(f)  # Load the .ibw file using igor2

        wave = ibw_obj['wave']  # Extract wave data
        return self._read_parms(wave)
