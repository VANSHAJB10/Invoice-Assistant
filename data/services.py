default_service_list ={
    "Web Development": 20000.00,
    "Social Media": 8000.00,
    "SEO Services": 12000.00,
    "Content Writing": 5000.00, 
    "Graphic Design": 7000.00,
    "Digital Marketing": 15000.00,
}

service_list = default_service_list
change_service_list = False
count = 1

list_change = input("Press Enter for default service list and any other key to chnage service_list").strip().lower()
if list_change != "":
    change_service_list = True

if(change_service_list == True):
    service_list = {}
    number_of_services = int(input("How many services do you want to add?"))
    while count <= number_of_services:
        
        service_item = input("Enter service {count}: ")
        service_tem_price = float(input("Enter service price: "))

        #add service item and price to service_list dictionary
        service_list[service_item] = service_tem_price
        count += 1
else:
    print("Using default_service_list")