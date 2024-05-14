import argparse
import hashlib
import base64

def generate_license(appname, uuid=None, expire_date=None, level="basic",write_file=True):
    combined_string = appname + level
    if expire_date == None :
        expire_date='perm'
    if not uuid:
        combined_string += "OPEN_FOR_ALL_UUIDS"
    else:
        combined_string += uuid
    if expire_date:
        combined_string += expire_date
    hashed = hashlib.sha256(combined_string.encode()).digest()
    license_key = base64.b64encode(hashed).decode()
    license_key = license_key+'||'+expire_date
    if write_file :
        with open('./license.dat' , 'w') as f :
            f.write(license_key)
    return license_key


def main():
    parser = argparse.ArgumentParser(description="Verify the given license key.")
    parser.add_argument("appname", type=str, help="Name of the app ")
    parser.add_argument("--uuid", type=str, default=None, help='UUID for the license (optional if open for all, cmd=reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v ProductID   \n linux=cat /sys/class/dmi/id/product_uuid )')
    parser.add_argument("--expire", type=str, default=None, help="Expiration date in DD-MM-YYYY format (optional)")
    parser.add_argument("--level", type=str, choices=["basic", "plus"], default="basic", help="License level, can be 'basic' or 'plus'. Default is 'basic'.")
    args = parser.parse_args()
    if not args.uuid :
        args.uuid = None
    generate_license(args.appname.encode('utf-8'), args.uuid.encode('utf-8'), args.expire.encode('utf-8'), args.level)


if __name__ == "__main__":
    pass
