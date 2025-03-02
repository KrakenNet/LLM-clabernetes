from local import run_command


image_paths = [
    "/images/ceos.tar"
    ]


def setup_unavailable_images():
    for image in image_paths:
        run_command("kubectl cp /images/ceos.tar kube-system/kube-controller-manager-knius:/tmp", f"Copying {image} into kube-controller")