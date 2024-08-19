def log_plain_text(save_path:str, content:str):
    with open(save_path, mode='a') as f:
        f.write(content)
