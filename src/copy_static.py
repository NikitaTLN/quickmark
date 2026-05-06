import os
import shutil


def copy_static(static_dir, output_dir):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    shutil.copytree(static_dir, output_dir)
