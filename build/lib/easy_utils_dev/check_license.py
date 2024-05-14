import argparse
import hashlib
import base64 , subprocess , sys
from datetime import datetime

def generate_license(appname, uuid=None, expire_date=None ,level="basic"):
    combined_string = appname + level
    if not uuid:
        combined_string += "OPEN_FOR_ALL_UUIDS"
    else:
        combined_string += uuid
    if expire_date:
        combined_string += expire_date
    hashed = hashlib.sha256(combined_string.encode()).digest()
    license_key = base64.b64encode(hashed).decode()
    license_key = license_key+'||'+expire_date
    return license_key

def verify_license(license_key, appname, uuid=None, level="basic",return_dict=False):
    key = license_key
    license_key = key.split('||')[0]
    expire_date = key.split('||')[1]
    if uuid == 'auto' : 
        if 'win' in sys.platform :
            cli = 'reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v ProductID'
            uuid = subprocess.getoutput(cli).splitlines()[2].split(' ')[-1].replace('\n','')
        elif 'linux' in str(sys.platform) :
            uuid = subprocess.getoutput('cat /sys/class/dmi/id/product_uuid').replace('\n' , '')
        else :
            raise Exception("Not supported OS")
    expected_license_key = generate_license(appname, uuid, expire_date, level)
    # Decode the provided license key
    try:
        decoded_key_bytes = base64.b64decode(license_key)
    except:
        if return_dict : 
            return {'status' :  400 , 'message' : "400_INCORRECT_FORMAT" }
        return "400_INCORRECT_FORMAT"
    # Convert expected_license_key to bytes
    expected_key_bytes = base64.b64decode(expected_license_key)
    # Check if the license matches the expected key
    if expected_key_bytes == decoded_key_bytes:
        # If an expiration date is provided, verify it
        if expire_date != 'perm':
            current_date = datetime.now().date()
            expire_date_obj = datetime.strptime(expire_date, '%d-%m-%Y').date()
            if current_date > expire_date_obj:
                if return_dict : 
                    return {'status' :  400 , 'message' : "400_EXPIRED"  }
                return "400_EXPIRED"
        if return_dict : 
            return {'status' :  200 , 'message' : ""  }
        return "200"
    else:
        if return_dict : 
            return {'status' :  400 , 'message' : "400_LICENSE_NOT_VALID."  }
        return "400_LICENSE_NOT_VALID."
def main():
    parser = argparse.ArgumentParser(description="Verify the given license key.")
    parser.add_argument("license", type=str, help="License key to be verified")
    parser.add_argument("appname", type=str, help="Name of the app")
    parser.add_argument("--uuid", type=str, default=None, help="UUID for the license (optional if open for all)")
    parser.add_argument("--level", type=str, choices=["basic", "plus"], default="basic", help="License level, can be 'basic' or 'plus'. Default is 'basic'.")
    args = parser.parse_args()
    result = verify_license(args.license, args.appname, args.uuid, args.level)
    print(result)

if __name__ == "__main__":
    pass