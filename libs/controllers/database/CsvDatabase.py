
from libs.controllers.database import IDatabaseController
from libs.controllers.storage import IStorageController


class CsvDatabase(IDatabaseController): 

    def __init__(self, filename: str, storage_controller: IStorageController):
        self.storage_controller = storage_controller 
        self.filename = filename
        
        # ensure the file exists and open it
        self.storage_controller.ensure_exists(self.filename)
        self.handle = open(filename, 'a+')


    def store(self, timestamp, data):
        self.handle.write(f'{timestamp},{data}\n')
        self.handle.flush()


    def get(self, timestamp):
        self.handle.seek(0)
        for line in self.handle.readlines():
            if line.startswith(str(timestamp)):
                return line.split(',')[1]
        
        return None
    
    def get_all(self):
        self.handle.seek(0)
        return self.handle.readlines()
    
    def get_all_between(self, start, end):
        self.handle.seek(0)
        return [line for line in self.handle.readlines() if line.startswith(str(start)) and line.startswith(str(end))]
    
    def get_all_after(self, timestamp):
        self.handle.seek(0)
        return [line for line in self.handle.readlines() if line.startswith(str(timestamp))]
    
    def get_all_before(self, timestamp):
        self.handle.seek(0)
        return [line for line in self.handle.readlines() if line.startswith(str(timestamp))]
    
    def __del__(self):
        self.handle.close()
        
