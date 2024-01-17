class FrameStructure:
    total_length = 199

    type_length = 1
    source_address_length = 2
    destination_address_length = 2
    ttl_length = 3
    frame_num_length = 1
    ses_num_length = 2
    checksum_length = 2
    correction_length = 5

    type_index = 0

    @property
    def data_length(self):
        return self.total_length - (
                self.type_length +
                self.source_address_length +
                self.destination_address_length +
                self.ttl_length +
                self.frame_num_length +
                self.ses_num_length +
                self.checksum_length +
                self.correction_length
        )

    @property
    def source_address_start_index(self):
        return self.type_index

    @property
    def source_address_end_index(self):
        return self.source_address_start_index + self.source_address_length

    @property
    def destination_address_start_index(self):
        return self.source_address_end_index

    @property
    def destination_address_end_index(self):
        return self.destination_address_start_index + self.destination_address_length

    @property
    def ttl_start_index(self):
        return self.destination_address_end_index

    @property
    def ttl_end_index(self):
        return self.ttl_start_index + self.ttl_length

    @property
    def frame_num_start_index(self):
        return self.ttl_end_index

    @property
    def frame_num_end_index(self):
        return self.frame_num_start_index + self.frame_num_length

    @property
    def ses_num_start_index(self):
        return self.frame_num_end_index

    @property
    def ses_num_end_index(self):
        return self.ses_num_start_index + self.ses_num_length

    @property
    def data_start_index(self):
        return self.ses_num_end_index
