import os
# Get raw byte data from file or string. If file doesn't exist, will use file path as the string.
def get_byte_data(data: str = '') -> bytes:
    if data:
        if os.path.isfile(data) and os.path.exists(data):
            try:
                with open(data,'rb') as file:
                    lines = file.read()
            except FileNotFoundError as e:
                print(f'{data} not found.',e)
                raise
            except IOError as e:
                print(f'An I/O error occured when attempting to open {file}.',e)
                raise
        else:
            return data.encode()
    return lines