
import os
from pythonfmu.builder import FmuBuilder


if __name__ == '__main__':
    FMI_DIR = os.path.dirname(os.path.abspath(__file__))
   # sys.path.append(os.path.dirname(SCRIPT_DIR))

    # cwd = os.getcwd() # e' la directory base  /home/ubuntu/dt-rse-mosaik
    project_files = ['./src','./scripts/fmi/fmu_script/resources/configuration','./mosaik/requirements.txt']
   # os.chdir(FMI_DIR)
    fmu_to_build = FMI_DIR+'/fmu_script/fmu_mockup.py'
    dest_folder = FMI_DIR
 #   project_files = ['./src/digital_twin/bess.py']
 
    FmuBuilder.build_FMU(script_file=fmu_to_build, dest=dest_folder, project_files=project_files)




