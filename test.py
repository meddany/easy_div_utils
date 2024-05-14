from easy_utils_dev.generate_license import generate_license
from easy_utils_dev.check_license import verify_license

license = generate_license('orion',write_file=False)
print(license)