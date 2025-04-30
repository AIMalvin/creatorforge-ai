import requests

def download_file(url, output_path):
    r = requests.get(url)
    with open(output_path, 'wb') as f:
        f.write(r.content)
    return output_path
