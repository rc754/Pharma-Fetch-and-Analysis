#!/usr/bin/env python
# coding: utf-8

# In[1]:


from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.ast_node_interactivity = "all"
from bs4 import BeautifulSoup
import requests
import time
import re
import json
import csv
import pymongo
import pandas as pd
from string import ascii_lowercase as alc
headers={'User-Agent': 'Mozilla/5.0'}


# ## Scrap Urls for Medicines Listed Alphabetically and Saving then in a CSV File

# In[2]:


def scrape_medicine_urls():
    try:
        for alphabet in alc:
            url = "https://www.1mg.com/drugs-all-medicines?"
            page = requests.get(url,
                            headers=headers,
                            params={"label": str(alphabet)})
            soup = BeautifulSoup(page.text, 'lxml')
            count_int = 500
            product_per_page = 30
            total_page = count_int/product_per_page
            page_count = round(total_page)
            if (page_count<total_page): page_count = page_count+1
                
            url_list = []
            for index in range(1,(page_count+1)):
                print("iterating through page",index, "of", page_count)
                page_new = requests.get(url,
                            headers=headers,
                            params={"page": str(index),"label": alphabet})
                soup_new = BeautifulSoup(page_new.text, 'lxml')
                list_script = soup_new.find('script', attrs={'type': 'application/ld+json'})
                script_content = list_script.contents[0]
                script_itemList = json.loads(script_content)['itemListElement']

                for item in script_itemList:
                    url_list.append(item["url"])

                print("Length of url_list:", len(url_list))
                index = index+1
                time.sleep(5)

            filename = "1mg_url_list_" + alphabet + ".csv"
            pd.DataFrame(url_list).to_csv(filename,index=False)
            print("Saved URLS for medicine names starting with:",alphabet)
            print("")
            time.sleep(5)
            
    except:
        print("Error while scraping medicine URLS...")
            


# ## Import CSV and get the url list 

# In[5]:


def url_list_gen (alphabet):
    try:
        url_list = []
        file_path = f'1mg_url_list_{alphabet}.csv'

        with open(file_path, 'r') as csvfile:
            csvreader = csv.reader(csvfile)
            for row in csvreader:
                url_list.append(row[0])
        return url_list
    except:
        print("Error while reading CSV files...")


# ## Download HTML files for each medicine

# In[6]:


def download_html_pages():
    try: 
        for alphabet in alc:  # loop over first 4 alphabets
            index = 0
            url_list = url_list_gen(alphabet)
            for url in url_list:
                if index == 0:
                    index += 1 
                    continue
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, headers=headers)
                soup = BeautifulSoup(response.text, 'lxml')
                fp = f"_{alphabet}{index}.htm"
                with open(fp, "w", encoding="utf-8") as file:
                    file.write(str(soup))
                index += 1 
                if index == 500:
                    break
        print("Saved HTML files")
    except: 
        print("Error while downloading HTML pages...")


# ## Scarp details of medicine from HTML file

# In[5]:


def get_elements(soup):
    try:    
        div_elements = soup.select('div.flexColumn')
        dict_med = {}

        info_json_list = soup.find_all('script', attrs={'type': 'application/ld+json'})
        for element in info_json_list:
            if "manufacturer" in str(element):
                info_json = json.loads(element.contents[0])
                dict_med['id'] = re.search(r".+?([0-9]{4}[0-9]*)", info_json['url']).group(1)
                print(f"id :{dict_med['id']}") 
                dict_med['manufacturer'] = info_json['manufacturer']
                dict_med['nonProprietaryName'] = info_json['nonProprietaryName']
                dict_med['dosageForm'] = info_json['dosageForm']
                dict_med['activeIngredient'] = info_json['activeIngredient']
                dict_med['mechanismOfAction'] = info_json['mechanismOfAction']
                dict_med['interactingDrug'] = info_json['interactingDrug']
            
        if div_elements:
            med = div_elements[0]

            name_ele = med.select_one("div.col-6.marginTop-8.flex.alignFlexEnd > div > div > h1")
            name = name_ele.text.strip() if name_ele else print("Not found")
#             print(f"Name :{name}")
            dict_med["Name"] = name
            
            price_ele = med.select_one("span.l4Regular.PriceWidget__marginLeft__dk5gl.PriceWidget__strikeThrough__rJY6f")
            price = price_ele.text.strip() if price_ele else print("Not found")
            if price is not None:
                price = str(price)
                match = re.search(r'MRP ₹(.+)', price)
                if match:
                    price = match.group(1)
#                     print(f"Price: {price}")
                    dict_med["Price"] = price
                else:
#                     print("Price not found")
                    dict_med["Price"] =  " Not found "
            else:
#                 print("Not found")
                dict_med["Price"] =  " Not found "

            desc_ele = med.select_one("div.col-6.bodyRegular.textPrimary.marginTop-8")
            desc = desc_ele.text.strip() if desc_ele else print("Not found")
#             print(f"Description :{desc}")
#             print()
            dict_med["Description"] = desc

            pro_ele = med.select_one("div:nth-child(27) > div.col-6.marginTop-8.GeneralDescription__htmlNodeWrapper__h23K3")

            pro = pro_ele.text.strip() if pro_ele else print("Not found")
#             print(f"Product Info :{pro}")
#             print()
            dict_med["Product Info"] = pro

            use_ele = med.select_one("div.col-6.marginTop-8.GeneralDescription__htmlNodeWrapper__h23K3 > ul > li > a")
            use = use_ele.text.strip() if use_ele else print("Not found")
#             print(f"Used for :{use}")
#             print()
            dict_med["Uses"] = use

            bene_ele = med.select_one("div.col-6.marginTop-8.GeneralDescription__htmlNodeWrapper__h23K3 > div")
            bene = bene_ele.text.strip() if bene_ele else print("Not found")
#             print(f"Benefits :{bene}")
#             print()
            dict_med["Benefits"] = bene

            side_ele = med.select("div.col-6.marginTop-8.GeneralDescription__htmlNodeWrapper__h23K3 > div > ul > li")
            side_list = [side.text for side in side_ele]
#             print(f"Side Effects :{side_list}")
#             print()
            dict_med["Side Effects"] = side_list

            work_ele = med.select_one("div:nth-child(37) > div.col-6.marginTop-8.GeneralDescription__htmlNodeWrapper__h23K3")
            work = work_ele.text.strip() if work_ele else print("Not found")
#             print(f"Working :{work}")
#             print()
            dict_med["Workings"] = work

        match = re.search(r"factBoxData\":(.+?),\"userResponses", str(soup))
        if match:
            factBoxData = match.group(1)
            factboxDict = {}
            for label in json.loads(factBoxData)['attributesData']:
                factboxDict[label['ga_label']] = label['value']   
#             print(f"Factbox: {factboxDict}")
            dict_med['Factbox'] = factboxDict

        match = re.search(r"productSubstitutes\":(.+?),\"productHighLight", str(soup))
        if match:    
            productSubstitutes = match.group(1)
            if (productSubstitutes != "null"):
                productSubList = []
                for label in json.loads(productSubstitutes)['attributesData']:
                    productSubList.append({"Name":BeautifulSoup(label['header'],"html.parser").text,"id":label['id']})
#                 print(f"Substitute: {productSubList}")
                dict_med['Substitute'] = productSubList

        print("-----------------")
        return dict_med
    except:
        print("Error while scraping details of medicine...")


# ## Call function to scrap the medicine details and Store in MongoDB

# In[6]:


def get_elements_super():
    try:
        list_med =[]
        
        for alphabet in alc:
            for i in range(1, 500):
                filename = f"_{alphabet}{i}.htm"
                with open(filename, "r", encoding="utf-8") as file:
                    html = file.read() 
                soup = BeautifulSoup(html, "lxml")
                print()
                print(f"Scraping elements from file: {filename}")
                med_dict = get_elements(soup)
                if bool(med_dict):
                    list_med.append(med_dict)
        print("Stored data as a list of dictionaries")
        return list_med
    except: 
        print("Error while scraping html pages...")


# ## Store Data in MongoDB

# In[7]:


def store_in_mongodb(med_list):
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017")
        database = client["Medicines"]
        collection = database["Medicines"]
        for med in med_list:
            collection.insert_one(med)
        print("Stored data in MongDB")
    except: 
        print("Error while storing data in Mongodb...")


# In[8]:


##scrape medicine urls
scrape_medicine_urls()
##download html for each medicine
download_html_pages()
##store the information as list of dictonary 
med_list = get_elements_super()
##store the data on monodb
store_in_mongodb(med_list)


# In[ ]:


## saving as a CSV for ML project
import pandas as pd
pd.DataFrame(med_list).to_csv("Final_Project_1mg_medicines.csv",index=False)

