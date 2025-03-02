from local import run_command
import os

image_directory = "/images/"

def setup_unavailable_images():
    image_files = [f for f in os.listdir(image_directory) if os.path.isfile(os.path.join(image_directory, f))]

    for image in image_files:
        image_path = os.path.join(image_directory, image)
        run_command(f"kubectl cp {image_path} kube-system/kube-controller-manager-knius:/tmp", f"Copying {image} into kube-controller")

setup_unavailable_images()
