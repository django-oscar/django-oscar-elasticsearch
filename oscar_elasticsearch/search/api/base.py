class BaseModelIndex:
    INDEX_NAME = None
    INDEX_MAPPING = None
    INDEX_SETTINGS = None
    Model = None

    def get_index_name(self):
        return self.INDEX_NAME

    def get_index_mapping(self):
        return self.INDEX_MAPPING

    def get_index_settings(self):
        return self.INDEX_SETTINGS

    def get_model(self):
        return self.Model
