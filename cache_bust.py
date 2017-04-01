import os
from flask import request


# inspired by https://gist.github.com/Ostrovski/f16779933ceee3a9d181
def create_hash(endpoint, values, app):
    if 'static' == endpoint or endpoint.endswith('.static'):
            filename = values.get('filename')
            if filename:
                if '.' in endpoint:  # has higher priority
                    blueprint = endpoint.rsplit('.', 1)[0]
                else:
                    blueprint = request.blueprint  # can be None too

                if blueprint:
                    static_folder = app.blueprints[blueprint].static_folder
                else:
                    static_folder = app.static_folder

                param_name = 'h'
                while param_name in values:
                    param_name = '_' + param_name
                values[param_name] = static_file_hash(
                    os.path.join(static_folder, filename))


def static_file_hash(filename):
    return int(os.stat(filename).st_mtime)
