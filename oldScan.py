
import tabula 
import pandas as pd 
import sys
import pdfplumber
import re


patternEA = "[a-zA-Z0-9]+\s[EA]+\s[0-9]"
patternPR = "^[a-zA-Z0-9]+\s[PR]+\s[0-9]"
patternH = "HCPCS:"
patternNum = "((\d+)((\.\d{1,2})?))$"
patternApost = "[0-9] +\" "

patternCent = "[0-9]+%"
repl = ""

class PDF_READER:
    def __init__(self, fname):
        self.fname = fname

    def read_quantum_pdf(self):
        df = pd.concat(tabula.read_pdf(self.fname, 
        pages = 'all',
        lattice = True,
        guess = False, 
        area = (272.16, 25.92, 685.44, 586.8),
        multiple_tables = True))

        return df

    def read_tilite_pdf(self):
        df = pd.concat(tabula.read_pdf(self.fname, 
        pages = 'all',
        lattice = False,
        guess = False,
        area = (343, 18, 641, 595),
        multiple_tables = True))

        return df


    def clean_tilite_pdf(self, df):
        df = df.iloc[1:]

        df.rename(columns = {"Unnamed: 0" : "Qty",  "Unnamed: 1" : "UOM" ,"Unnamed: 2" : "Qty" })
        return df


    #Reads a sunprise pdf and returns a pandas dataframe of all of the wanted data
    #Assumes the only thing we care about are things with HCPS and a Price < 0 assocatied with them.
    def read_sunrise_pdf(self):

        #Column names (My understanding is we only care about Item-Number, Qty, and Ext Price.... I kept some extras can easily remove or add others from pdf)
        columns = ['Item Number','UM', 'Qty Ordered', 'Qty Shipped', 'Qty Open', 'HCPC', 'Ext Price']

        df = pd.DataFrame(columns = columns)

        with pdfplumber.open("SunriseMore.pdf") as f:
            #Set Bools
            EAPR= False
            HCPC = False
    
            #Row to be appended to the dataframe
            row = ['Nan',  'Nan', '0', '0', '0','Nan', '0' ]

            #Loop through each page
            for page in f.pages:
                
                #Extract each indiivdual line
                lines = page.extract_text().splitlines()
                
                #loop through each of these lines
                for index, line in enumerate(lines):
                    if(index < 100):
                        print(line)
                   
                    #Get rid of %'s and " 
                    line = re.sub(patternCent, repl, line)
                    line = re.sub(patternApost, repl, line)

                    #If the HCPC and other data line have been accounted for then write to the dataframe 
                    if(EAPR and HCPC):
                        
                        df.loc[len(df)] = row
                        EAPR= False
                        HCPC = False
                    
                        row = ['Nan',  'Nan', '0', '0', '0','Nan', '0']
                   

                    #If it is data we care about (Checks if it contains (Number-EA|PR-Number)
                    if(re.search(patternEA, line) or re.search(patternPR, line)):
                        
                        EAPR= True
                     
                        list = line.split()
                    
                        row[0] = list[0] #Extract the Item Number
                        row[1] = list[1] #Extract the UM (not sure what this is.... Either EA or PR)
                        

                        #Ensure that these values exists in the pdf.
                        if(len(list) > 2):
                            row[2] = list[2] #Extract Quantity Ordered
                        if(len(list) > 3):
                            row[3] = list[3] #Extract Quantity Shipped
                            if(len(list) > 4):
                                row[4] = list[4] #Extract quantity Open

                        #Move to next index
                        list = lines[index + 1]

                        #Move to next line to find extended cost make sure it has a cost and it is not a HCPC
                        if not re.search(patternH, list):
                            
                            list = list.split()
                            
                            #Check if it is a number
                            if(re.search(patternNum, list[-1])):
                                try:
                                    num = float(list[-1]) #Double checks it is a number that follow their decimal format.
                                    
                                    row[6] = num  #Extract Extended Cost
                                    continue

                                except: #This means that there is no cost and we don't care or it was a line we didnt care about because it didn't contain a number.
                                    continue  #This is not a number so ignore it.       
                            else:
                                continue #Move on to the next Line


                    else:
                    #Didn't find something with previous data so we need to check if it is a line that contains a HCPC
                        list = line.split()
                        if(re.search(patternH, line)):
                            HCPC = True #Stores that we found a HCPC and we need to write it
                            row[5] = list[1] #Extract the HCPC
                        else:
                            if EAPR:
                                 df.loc[len(df)] = row
                                 EAPR= False
                                 HCPC = False
                    
                                 row = ['Nan',  'Nan', '0', '0', '0','Nan', '0']

        #Sorted data as a pandas dataframe       
        return df

    def new_sunrise(self):

        EAPR = False
        HCPC = False

        columns = ['Item Number','UM', 'Qty Ordered', 'Qty Shipped', 'Qty Open', 'HCPC', 'Ext Price']
        row = ['Nan',  'Nan', '0', '0', '0','Nan', '0' ]
        df = pd.DataFrame(columns = columns)
        index = 0
        with pdfplumber.open(self.fname) as pdf:
            index = 0
            for page in pdf.pages:
                index = 0

                if EAPR:
                    EAPR = False
                    HCPC = False
                    df.loc[len(df)] = row
                    row = ['Nan',  'Nan', '0', '0', '0','Nan', '0' ]
                
                lines = page.extract_text().splitlines()
                
                while(index < len(lines)):
                    lines[index] = re.sub(patternCent, repl, lines[index])
                    lines[index] = re.sub(patternApost, repl, lines[index])

                    list = lines[index].split()

                    if EAPR:
                        if(re.search(patternEA, lines[index]) or re.search(patternPR, lines[index]) or HCPC):
                            EAPR = False
                            HCPC = False
                            df.loc[len(df)] = row
                            row = ['Nan',  'Nan', '0', '0', '0','Nan', '0' ]
                            continue
                        else:
                            if  re.search(patternH, lines[index]): #And EAPR is True
                                row[5] = list[1] #Extract the HCPC
                                HCPC = True
                                continue
                            else:
                                  if(re.search(patternNum, list[-1]) and re.search(patternDec, list[-1]) and EAPR):
                                   
                                    try:

                                        num = float(list[-1]) #Double checks it is a number that follow their decimal format.
                                     
                                        row[6] = num  #Extract Extended Cost
                                     
                                    except:
                                        index+=1
                                        continue
                    else:
                        if(re.search(patternEA, lines[index]) or re.search(patternPR, lines[index])):
                            EAPR = True 
                            # print(lines[index].split())
                            row[0] = list[0] #Extract the Item Number
                            row[1] = list[1] #Extract the UM (not sure what this is.... Either EA or PR)

                            #Ensure that these values exists in the pdf.
                            if(len(list) > 2):
                                row[2] = list[2] #Extract Quantity Ordered
                                if(len(list) > 3):
                                    row[3] = list[3] #Extract Quantity Shipped
                                    if(len(list) > 4):
                                        row[4] = list[4] #Extract quantity Open
                            
                            #index+=1
                    index+=1
            df = df[df['Ext Price'] != "0"]
            df = df[df['Ext Price'] != 0]
            print(df)
            return df

    def write_csv(self, sorted_table):
        sorted_table.to_csv('test3.csv', mode = 'w', index = False)

if __name__ == "__main__":
    reader = PDF_READER(sys.argv[1])
    # print(reader.read_tilite_pdf())
    reader.write_csv(reader.read_sunrise_pdf())
   