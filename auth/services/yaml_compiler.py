import yaml

class YamlCompiler:
    @classmethod
    def read_file(self, file_path):
        with open(file_path) as file:
            return yaml.safe_load(file)
    
    @classmethod
    def write_file(self, file_path, operation, data):
        print(file_path)
        with open(file_path, operation) as file:
            print(data)
            yaml.safe_dump(data, file, default_flow_style=False)