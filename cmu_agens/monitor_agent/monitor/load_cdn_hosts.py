import json
import os

## Read Azure location file and generate coordinates for All Azure locations
def load_cdn_hosts():
    ## Read the azure-loc.csv file to draw the planetlab node locations
    vm_list = {}
    script_folder = os.path.dirname(os.path.realpath(__file__))

    cdns = json.load(open(script_folder + "/cdn-urls.json"))
    return cdns

if __name__ == "__main__":
    cdns = load_cdn_hosts()
    print cdns