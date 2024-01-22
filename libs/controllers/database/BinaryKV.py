from libs.controllers.storage.LocalStorage import LocalStorageController
from libs.controllers.database import IDatabaseController
from libs.controllers.storage import IStorageController
from libs.external.ChannelLogger import logger

import libs.external.umsgpack as umsgpack

class BinarKVDatabase(IDatabaseController):
    """ 
        store the data in a binary format. 
        
        this database stores the data in a binary format. this format is as follows: 
            - 4 bytes: total length of the data
            - 4 bytes: timestamp
            - the rest: the data in a msgpack format

        this format is used to make it easy to read the data from the file.
        however, this database has a few drawbacks: 
            - searching of data in a range is extremely slow
                - the data is not indexed or sorted in any way other then insertion order
            - if compression is wanted data is not immediately stored
                - the data will be stored in a buffer until it is 
            - the entire file has to be read to get the data 

            - if compression is wanted the entire file needs to be insert or read measuremnts
    """

    def __init__(self, filename: str, storage_controller: IStorageController):
        self.storage_controller = storage_controller
        self.filename = filename

        # ensure the file exists and open it
        self.storage_controller.ensure_exists(self.filename)
        self.handle = open(filename, 'a+b')

    def store(self, timestamp, data):
        """ store the data in a binary format. the first 32 bits are the timestamp, the rest is the data"""
        binary = umsgpack.dumps((timestamp, data))

        # encoded "total length of the data" + "timestamp" + "data"
        self.handle.write(len(binary).to_bytes(4, 'big') + timestamp.to_bytes(4, 'big') + binary)
        self.handle.flush()

    def get(self, timestamp):
        self.handle.seek(0)

        # read only the bytes we need 
        while True:
            line = self.handle.read(8)
            if not line:
                break

            ts = int.from_bytes(line[4:8], 'big')
            if ts == timestamp:
                d = self.handle.read(int.from_bytes(line[0:4], 'big'))
                return umsgpack.loads(d)

            # move to the next line
            self.handle.seek(int.from_bytes(line[0:4], 'big'), 1)

        return None

    def get_all(self):
        self.handle.seek(0)
        data = []

        while True:
            line = self.handle.read(8)
            if not line:
                break

            d = self.handle.read(int.from_bytes(line[0:4], 'big'))
            data.append(umsgpack.loads(d))

        return data

    # FIXME:: FIX THESE FUNCTIONS 
    def get_all_between(self, start, end, inclusive=False):
        """ FUNCTION WILL ONLY RETURN ERROR """
        self.handle.seek(0)
        data = []
        while True:
            line = self.handle.read(8)
            if not line:
                break

            ts = int.from_bytes(line[4:8], 'big')
            if ts > start and ts < end or (inclusive and (ts == start or ts == end)):
                d = self.handle.read(int.from_bytes(line[0:4], 'big'))
                data.append(umsgpack.loads(d))

            else:
                # move to the next line
                self.handle.seek(int.from_bytes(line[0:4], 'big'), 1)

        return data

    def get_all_after(self, timestamp, inclusive=False):
        """ FUNCTION WILL ONLY RETURN ERROR """
        self.handle.seek(0)
        data = []

        while True:
            line = self.handle.read(8)
            if not line:
                break

            ts = int.from_bytes(line[4:8], 'big')
            if ts > timestamp or (inclusive and ts == timestamp):
                d = self.handle.read(int.from_bytes(line[0:4], 'big'))
                data.append(umsgpack.loads(d))

            else:
                # move to the next line
                self.handle.seek(int.from_bytes(line[0:4], 'big'), 1)

        return data

    def get_all_before(self, timestamp, inclusive=False):
        """ FUNCTION WILL ONLY RETURN ERROR """
        self.handle.seek(0)
        data = []

        while True:
            line = self.handle.read(8)
            if not line:
                break

            ts = int.from_bytes(line[4:8], 'big')
            if ts < timestamp or (inclusive and ts == timestamp):
                d = self.handle.read(int.from_bytes(line[0:4], 'big'))
                data.append(umsgpack.loads(d))

            else:
                # move to the next line
                self.handle.seek(int.from_bytes(line[0:4], 'big'), 1)

        return data
    
    def __del__(self):
        self.handle.close()
        