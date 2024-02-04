import os

cwd = os.getcwd()

images_path = os.path.join(cwd, 'images')
calibration_path = os.path.join(images_path, 'configuration')
scan_path = os.path.join(images_path, 'scans')

config_path = os.path.join(cwd, 'configuration')
calibration_images_path = os.path.join(config_path, 'images')

scans_path = os.path.join(cwd, 'scans')

if not os.path.exists(calibration_images_path):
    os.makedirs(calibration_images_path)

if not os.path.exists(scans_path):
    os.makedirs(scans_path)

