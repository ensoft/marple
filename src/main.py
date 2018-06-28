import sys
from src.modules import controller

if __name__ == "__main__":
    # Call main function with command line arguments
    # Excluding argv[0] (program name)
    controller.main(sys.argv[1:])
