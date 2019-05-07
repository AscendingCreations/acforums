from .yaml_compiler import YamlCompiler
import sass

class ScssCompiler:
    sass_variables = ""
    def __init__(self, variables_file):
        variables = YamlCompiler.read_file(variables_file)
        for key, val in variables.items():
            self.sass_variables += "\n${0}: {1};".format(key, val)

    def compile(self, file):
        return sass.compile(
            string="""
            {1}
            @import '{0}';
            """.format(file, self.sass_variables),
            output_style='compressed'
        )

    def write_file(self, scss, file_path):
        with open(file_path, 'w') as file:
            file.write(scss)