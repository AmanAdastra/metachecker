from datetime import datetime
import pybars

def read_file(file_name):
    f = open(file_name, "rb")
    return f.read()

def dynamic_html(file_path,**kwargs):
    template_string = read_file(file_path)
    replacements = {key: value for key, value in kwargs.items()}
    compiler = pybars.Compiler()
    template = compiler.compile(str(template_string,"utf-8"))
    return template(replacements)

