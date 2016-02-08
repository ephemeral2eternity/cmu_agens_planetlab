import csv
import os

## Read Azure location file and generate coordinates for All Azure locations
def load_vms():
    ## Read the azure-loc.csv file to draw the planetlab node locations
    vm_list = {}
    script_folder = os.path.dirname(os.path.realpath(__file__))
    with open(script_folder + "/vms.csv", 'rU') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        for row in csvreader:
            vm_name = row[0]

            vm_ip = row[1]
            vm_zone = row[2]
            ## vm_list[vm_name] = {'ip' : vm_ip, 'zone' : vm_zone}
            vm_list[vm_name] = vm_ip

    return vm_list

if __name__ == "__main__":
    vms = load_vms()
    print vms
