
class IDatabaseController: 

    def store(self, timestamp, data): 
        raise NotImplementedError()
    
    def get(self, timestamp):
        raise NotImplementedError()
    
    def get_all(self):
        raise NotImplementedError()
    
    def get_all_between(self, start, end):
        raise NotImplementedError()
    
    def get_all_after(self, timestamp):
        raise NotImplementedError()
    
    def get_all_before(self, timestamp):
        raise NotImplementedError()