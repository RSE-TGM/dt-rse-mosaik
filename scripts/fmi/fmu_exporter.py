import os
import argparse
from pathlib import Path
from pythonfmu.builder import FmuBuilder


def get_args():
    parser = argparse.ArgumentParser(description="FMU Exporter of Digital Twin (RSE)",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--source",
                        action="store",
                        default="./fmu_script/fmu_mockup.py",
                        type=str,
                        help="Specifies the python file which we want to create the FMU from."
                        )
    parser.add_argument("--dest",
                        action="store",
                        default="./fmu/",
                        type=str,
                        help="Specifies the destination folder where to save the FMU file."
                        )
    parser.add_argument("--project_files",
                        nargs='*',
                        action="store",
                        default=[],
                        help="Specifies the project files for the creation of FMU (still don't know what it means)."
                        )

    input_args = vars(parser.parse_args())
    return input_args


if __name__ == '__main__':
    args = get_args()

    import os
    cwd = os.getcwd()

    source = args['source']
    dest = args['dest']
    project_files = args['project_files']

    fmu_to_build = source
    dest_folder = dest
    project_files = project_files
    FmuBuilder.build_FMU(script_file=fmu_to_build, dest=dest_folder, project_files=project_files)
