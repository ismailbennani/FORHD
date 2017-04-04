import argparse
import os

from FORHD import Main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run FORHD server')
    parser.add_argument('-v', dest='verbose', action='store_const',
                       const=True, default=False,
                       help='verbose (default : False)')

    args = parser.parse_args()

    os.chdir("FORHD")
    Main(verbose = args.verbose)
