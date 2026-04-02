from app.app import EldenApp
import faulthandler

if __name__ == "__main__":
    faulthandler.enable()
    EldenApp()