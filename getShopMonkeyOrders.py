import json
import os
import time
import requests
import math
import os
import time
import json
import gspread


## TIMER
startTime = time.time()

#API KEYS
PUB = "PUBLIC_KEY"
PRIV = "PRIVATE_KEY"

#Create new refined File
with open('JSON/refined_sm_orders.json','w') as f:
    f.writelines("[")
    f.close

## SAVING TO GOOGLE SHEETS --------------------------------------------------------------------------------------------------------------------------------------------

sa = gspread.service_account(filename="credentials/orderCreds.json")
sh = sa.open("Order Sheet")
wks = sh.worksheet("SM")

orderCount = 0
callCount = 0

#Write info to Google Sheets
def LogInfo():

    global callCount, orderCount
    row_count = 0

    orderCount=0
    with open("JSON/refined_sm_orders.json") as f:
        for line in f:
            orderCount += 1

    ## Modify Tab Row Count 
    def modRowCount(worksheet):
            global callCount, orderCount
            if(row_count<(orderCount)):
                print("Adding Rows..")
                new=orderCount-row_count
                worksheet.add_rows(new)
                callCount += 1

            else:
                if(row_count>(orderCount)):
                    print("Deleting rows")
                    worksheet.delete_rows((orderCount+1),row_count)
                    callCount += 1

    if callCount <= 59:
                modRowCount(wks)
                #i += 1
                callCount += 1
    else:
                callCount = 0
                print("Taking a snooze..")
                time.sleep(60)
                modRowCount(wks)
                #i += 1
                callCount += 1
    #Write info 
    i = 0
    f = open('JSON/refined_sm_orders.json')
    data = json.load(f)

    print("Writing Data..")
    for x in data:
        number = x["Number"]
        firstName = x["FirstName"]
        lastName = x["LastName"]
        vehicle = x["Vehicle"]
        poNumber = x["PONumber"]
        created = x["Created"]
        completed = x["Completed"]
        workFlow = x["WorkFlow"]
        location = x["Location"]
        state = x["State"]
        address = x["Address"]
        phone = x["Phone"]
        email = x["Email"]

        if callCount <= 58:
            wks.update("A"+str(i+2)+":m"+str(i+2),[[number,firstName,lastName,vehicle,address,state,phone,email,poNumber,created,completed,workFlow,location]])
            i += 1
            callCount += 1
        else:
            callCount = 0
            print("Taking a snooze..")
            time.sleep(60)
            wks.update("A"+str(i+2)+":m"+str(i+2),[[number,firstName,lastName,vehicle,address,state,phone,email,poNumber,created,completed,workFlow,location]])
            i += 1
            callCount += 1


#Get Shop Monkey Bearer Token
def getToken(PUB, PRIV):
    
    url = "https://api.shopmonkey.io/v2/token"

    payload = {
        "publicKey": PUB,
        "privateKey": PRIV
    }
    headers = {
        "Accept": "text/html",
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)
    return(response.text)

#Get orders from ShopMonkey Location
def getSMOrders(PUB, PRIV):
    token = getToken(PUB, PRIV)
    i = 100
    offset = 0
    while i == 100:
        
        url = "https://api.shopmonkey.io/v2/orders?limit=100&offset="+str(offset)+"&sort=creationDate&isArchived=false"

        payload = {
        "publicKey": PUB,
        "privateKey": PRIV
        }

        headers = {
        "Accept": "application/json",
        "Authorization": "Bearer "+token
        }
        response = requests.request("GET", url, json=payload, headers=headers)
        data = response.json()

        # Writing to temp file
        # Create temp file
        with open("JSON/tempOrders.json", "w") as f:
            f.write("[")
        with open("JSON/tempOrders.json", "a") as f:
            json.dump(data, f)
        f.close()

        ## Refine json output
        with open('JSON/tempOrders.json') as f:
            contents = f.read()
            #Create new lines for each entry
            contents = contents.replace('{"authorizedDate"', '\n{"authorizedDate"')
        with open("JSON/tempOrders.json", 'w') as f:
            f.writelines(contents)

        with open('JSON/tempOrders.json') as f:
            contents = f.read()
            contents = contents.replace('[\n', '[')
            #Remove "[" & "]"
            contents = contents.replace('[{"authorizedDate"', '{"authorizedDate"')
            contents = contents.replace('}}]', '}},')
        with open("JSON/tempOrders.json", 'w') as f:
            f.writelines(contents)

        with open("JSON/tempOrders.json", 'rb+') as f:
            f.seek(-1, os.SEEK_END)
            f.truncate()
        with open("JSON/tempOrders.json", "a") as f:
            f.write("]")
        f.close()

        #Get number of records received this will determine if this will loop again
        counter=0
        with open("JSON/tempOrders.json") as f:
            for line in f:
                counter += 1
        offset += 100
        i = counter

        #Gather Information
        def dateFormat(date):
            try:
                date = date[:10]
                year = date[:4]
                month = date[5:7]
                day = date[8:]
                date = month+"/"+day+"/"+year
            except:
                date=""
            return date

        def nullCheck(var):
                if var is None:
                    var = " "
                else:
                    var = var
                return var

        def getCustomerInfo(id,PUB,PRIV):
            token = getToken(PUB,PRIV)
            #print(id)

            url = "https://api.shopmonkey.io/v2/customers?id="+id+"&sort=creationDate&offset=0&limit=50&includeShopmonkeyCustomers=false"

            headers = {
                "Accept": "application/json",
                "Authorization": "Bearer "+token
            }

            response = requests.request("GET", url, headers=headers)
            info = (response.json())

            # Writing to temp file
            with open("JSON/tempCustomer.json", "w") as f:
                json.dump(info, f)
            f.close()
            f = open('JSON/tempCustomer.json')
            info = json.load(f)


            for i in info:
                address1 = nullCheck(i["address1"])
                address2 = nullCheck(i["address2"])
                city = nullCheck(i["city"])
                state = nullCheck(i["state"])
                zipcode = nullCheck(i["zip"])
                try:
                    address = address1+" "+address2+", "+city+", "+str(zipcode)
                    address = address.replace(" ,  , ","")
                except:
                    address=" "
                try:
                    #phone = str(phone)
                    phone = str(i["phones"])
                    phone = phone[4:-2]
                except:
                    phone = " "

                try:
                    #email = str(email)
                    email = str(i["emails"])
                    email = email[2:-2]
                except:
                    email = " "

            return address,state,phone,email

        #IDs of Workflows that we want
        workflows = ["5c48a401c025170a852ea921", "602c0c5c60db34024fde3553", "5dd59bd959f347157d98ad91", "5cd9aef138c6770a9f82e8f6", "60a5bda23e6f595d0341d9d8", "5d2a102d89e0e90a933a4e82", "614b8a29d89dfc29bf2cccaf", "614b8a2bd89dfce2ee2cccb1", "614b8a2c006e30a838419062", "614b8a2e34e7dd54b07a6ac1", "614b8a2f6f43d3344ab1fc4a", "614b8a310a28afa45b766c49", "5a4f578cb9658d5dcf633c39", "60cb640ae0aeea75e7c1ad5b", "5b6760ddf00230183405e524", "5b67613ff00230183405e531", "5a4f578cb9658d5dcf633c3a", "6092e3e32ebbf86836d9f02a"]

        def characterFilter(string):
            string = string.replace("	","")
            return string

        def getTags(data):
            tags = []
            for d in data:
                tag = (str(d["name"])).replace(",","")
                tag = tag.replace("\\","")
                tags.append(tag)
            
            tags = ', '.join(tags)
            return tags


        f = open('JSON/tempOrders.json')
        data = json.load(f)
        for d in data:
            for w in workflows:
                
                if w == d["workflowId"]:
                    number = d["number"]
                    firstName = d["customer"]["firstName"]
                    lastName = d["customer"]["lastName"]
                    model = d["vehicle"]["model"]
                    year = d["vehicle"]["year"]
                    vehicle = characterFilter(str(year)+" "+model)
                    poNumber = d["poNumber"]
                    created = dateFormat(d["creationDate"])
                    completed = dateFormat(d["completedDate"])
                    workflow = d["workflow"]
                    customerinfo = getCustomerInfo(d["customer"]["shopmonkeyId"],PUB,PRIV)
                    state = customerinfo[1]
                    address = customerinfo[0]
                    phone = customerinfo[2]
                    email = customerinfo[3]
                    tags = getTags(d['tags'])

                    with open('JSON/refined_sm_orders.json','a') as fout:
                        fout.writelines('{"Number": "'+str(number)+'", "FirstName": "'+firstName+'", "LastName": "'+lastName+'", "Vehicle": "'+vehicle+'", "Address": "'+address+'", "State": "'+state+'", "Phone": "'+phone+'", "Email": "'+email+'", "PONumber": "'+poNumber+'", "Created": "'+created+'", "Completed": "'+completed+' ", "WorkFlow": "'+workflow+'", "Location": "'+LOCATION+'", "Tags": "'+tags+'"},')
                        fout.writelines('\n')
                        fout.close()
                    break


#Call Function with Location credentials
getSMOrders(PUB,PRIV)


#Close JSON
with open("JSON/refined_sm_orders.json", 'rb+') as f:
    f.seek(-3, os.SEEK_END)
    f.truncate()
with open('JSON/refined_sm_orders.json', 'a') as f:
    f.writelines("]")

LogInfo()

os.remove("JSON/tempOrders.json")
os.remove("JSON/tempCustomer.json")


#Find Execution Time
seconds = (time.time() - startTime)
minutes = seconds/60
remainder = minutes
minutes = math.modf(minutes)
minutes = int(minutes[1]) #FINAL
seconds = (remainder - minutes)*60 #FINAL
finalTime= (str(minutes)+":"+str(seconds))[:9]
print(finalTime)