import ctypes
import os
import time

# --- Configuration ---
DLL_PATH = "./parser.dll"
# !!! IMPORTANT: CHANGE THIS TO A VALID SAVE FILE PATH !!!
SAVE_FILE_PATH = "D:\\Python\\save_parser\\borjom.sl2"
CHARACTER_SLOT_TO_TEST = 0

def run_smoke_test():
    """
    Tests if the C library can be loaded and a function can be called.
    """
    print("--- Python C Library Smoke Test ---")

    # 1. Check if the DLL and save file exist before we start
    if not os.path.exists(DLL_PATH):
        print(f"Error: Cannot find the DLL. Make sure '{DLL_PATH}' is in the same directory.")
        return

    if not os.path.exists(SAVE_FILE_PATH):
        print(f"Error: Cannot find the test save file at '{SAVE_FILE_PATH}'.")
        print("Please update the SAVE_FILE_PATH variable in this script.")
        return

    # 2. Load the C library
    try:
        parser_lib = ctypes.CDLL(DLL_PATH)
        print(f"Successfully loaded '{DLL_PATH}'")
    except OSError as e:
        print(f"Error loading DLL: {e}")
        print("This can happen if the DLL is 32-bit and Python is 64-bit (or vice-versa).")
        return

    # 3. Define the function signature (prototype) for the function we want to call.
    #    This tells ctypes what kind of arguments the function expects and what it returns.
    try:
        update_data = parser_lib.update_character_data
        update_data.argtypes = [ctypes.c_char_p, ctypes.c_int] # (const char*, int)
        update_data.restype = ctypes.c_int                    # returns int
        print("Successfully found 'update_character_data' function.")
    except AttributeError:
        print("Error: Could not find the 'update_character_data' function in the DLL.")
        print("Check if you used the '__declspec(dllexport)' macro correctly in your C code.")
        return

    # 4. Prepare the arguments
    #    ctypes can't pass Python strings directly, they must be encoded to bytes.
    filepath_bytes = SAVE_FILE_PATH.encode('utf-8')

    # 5. Call the C function
    print(f"\nCalling C function: update_character_data('{SAVE_FILE_PATH}', {CHARACTER_SLOT_TO_TEST})")
    
    # This is where the magic happens. Python calls into your compiled C code.
    start = time.perf_counter()
    return_code = update_data(filepath_bytes, CHARACTER_SLOT_TO_TEST)
    end = time.perf_counter()

    start2 = time.perf_counter()
    return_code = update_data(filepath_bytes, CHARACTER_SLOT_TO_TEST)
    end2 = time.perf_counter()

    parser_lib.invalidate_headers()

    start3 = time.perf_counter()
    return_code = update_data(filepath_bytes, CHARACTER_SLOT_TO_TEST)
    end3 = time.perf_counter()

    # 6. Check the result
    print(f"\nC function finished and returned code: {return_code}")

    if return_code == 0:
        print("SUCCESS: The function reported success (returned 0).")
    elif return_code == -1:
        print("FAILURE: The function reported an error (file not found).")
    elif return_code == -2:
        print("FAILURE: The function reported an error (invalid file size).")
    elif return_code == -3:
        print("FAILURE: The function reported an error (memory allocation failed).")
    else:
        print(f"FAILURE: The function returned an unknown error code: {return_code}.")

    print(f"Initialize_headers duration: {end - start:.6f} seconds")
    print(f"Worktime duration: {end2 - start2:.6f} seconds")
    print(f"Duration after invalidation: {end3 - start3:.6f} seconds")

if __name__ == "__main__":
    run_smoke_test()