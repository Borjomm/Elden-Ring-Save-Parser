from parser import *

if __name__ == "__main__":
    SAVE_FILE_PATH = "D:\\Python\\save_parser\\after.sl2"
    SAVE_FILE_2 = "D:\\Python\\save_parser\\borjom.sl2"
    CHARACTER_SLOT_TO_TEST = 0

    result = update_data(SAVE_FILE_PATH, CHARACTER_SLOT_TO_TEST, header_mode=True)
    headers = get_headers()
    for header in headers:
        print(header.name)
    data = get_data()
    