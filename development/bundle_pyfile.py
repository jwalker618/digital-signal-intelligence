import os

FILE_PATH = "infrastructure/api/types.py"   # <--- change this as needed

def copy_py_to_txt(txt_file_path=None):
    """
    Copies the contents of a Python file (.py) to a text file (.txt).
    """
    file_path = FILE_PATH

    if not os.path.exists(file_path):
        print(f"Error: Source file '{file_path}' does not exist.")
        return
    
    base_name = os.path.splitext(file_path)[0]  # Remove .py extension
    txt_file_path = base_name + ".txt"
    
    try:
        with open(file_path, "r", encoding="utf-8") as py_file:
            content = py_file.read()
        
        with open(txt_file_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(content)
        
        print(f"Successfully copied '{file_path}' to '{txt_file_path}'.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    copy_py_to_txt()