
import pandas as pd 
import pdfplumber
import re
import glob

#Regex any number followed by two decimakl places. Many Quotes have this format for extended price
patternDec = "^\d*\.[0-9][0-9]$"
patternCent = "[0-9]+%"


class PDF_READER:

    def write_csv(self, sorted_table, name):
        sorted_table.to_csv('{}.csv'.format(name), mode='w', index=False)
    #Read quantum pdf returns a pandas dataframe with all of the needed information
    def read_quantum_pdf(self, fname):
        print(fname)
        columns = ['QuoteID', 'Item Number', 'Qty',
                   'MSRP', 'Ext Price', 'Vendor']
        row = ['100',  'Nan', '0', '0', '0', 'Quantum']


        #Dataframe to return
        df = pd.DataFrame(columns=columns)

        #Open the pdf
        with pdfplumber.open(fname) as pdf:
            index = 0

            for page in pdf.pages:
                index = 0
                lines = page.extract_text().splitlines()
                

                while(index < len(lines)):
                   
                    #Get rid of all $ characters
                    lines[index] = lines[index].replace("$", "")
                    list = lines[index].split()

                    #Get rid of all commas
                    lines[index] = lines[index].replace(",", "")
            
                    #Ensure that list is not empty before checking to prevent out of bounds errors
                    if(len(list) > 0):
                        if(re.search(patternDec, list[-1])):
                            
                            
                            try:
                                row[4] = list[-1] #Extended Price
                                row[3] = list[-3] #MSRP
                                row[2] = list[-4] #Quantity
                                row[1] = list[0] #item Number

                                df.loc[len(df)] = row #Add new row to dataframe
                                row = ['100',  'Nan', '0', '0', '0', 'Quantum'] #Reset the row

                            except:
                                #At end of the page need to return and exit
                                df = df[df['Ext Price'] != "0.00"]
                                self.write_csv(df, fname.strip(".pdf"))
                                return df

                    index+=1
        #Shouldn't reach here but return if we do
        df = df[df['Ext Price'] != "0.00"]
        self.write_csv(df, fname.strip(".pdf"))
        print(df)
        return df

     #Read tilite pdf returns a pandas dataframe with all of the needed information
    def read_tilite_pdf(self, fname):
        
        columns = ['QuoteID', 'Item Number', 'Qty', 'MSRP', 'Ext Price', 'Vendor']
        row = ['100',  'Nan', '0', '0', '0', 'Tilite']
    
        #Datafdrame to return
        df = pd.DataFrame(columns=columns)

        with pdfplumber.open(fname) as pdf:

            #reset index
            index = 0

            for pageNum, page in enumerate(pdf.pages):

                #If at the last page break. Tilite puts information we dont care about on the last page always. 
                if(pageNum + 1 == len(pdf.pages)):
                    break
                #reset Index
                index = 0
            
                lines = page.extract_text().splitlines()

                while(index < len(lines)):
                    list = lines[index].split()
                    #Get rid of the commas in the cost
                    list[-1] = list[-1].replace(",", "")
                    
                    #if it is in decimal format we want

                    if(re.search(patternDec, list[-1])):
                        if(not list[0].isnumeric()): #This means there is only an Item number and no UOM or QTY
                                row[1] = list[0] #Get Item Number
                        else:
                            row[2] = list[0] #Get the quantity if it exists
                            row[1] = list[2] #If quantity exists then this is the Item Number

                        row[4] = list[-1] #Ext cost
                        row[3] = list[-5] #MSRP

                        #add new row to dataframe
                        df.loc[len(df)] = row

                        #reset dataframe
                        row = ['100',  'Nan', '0', '0', '0', "tilite"]
                    

                    index +=1

        print(df)
        self.write_csv(df, fname.strip(".pdf"))
        return df
        
    def read_sunrise_pdf(self, fname):
        columns = ['QuoteID', 'Item Number', 'Qty',
                'MSRP', 'Ext Price', 'Vendor']
                
        row = ['100',  'Nan', '0', '0', '0', 'Sunrise']

        #df to return
        df = pd.DataFrame(columns=columns)

        
        with pdfplumber.open(fname) as pdf:
            index = 0
            for page in pdf.pages:
                index = 0
                lines = page.extract_text().splitlines()
                while(index < len(lines)):

                    #If total is in the line then I am assuming we are at the end
                    #This holds true for 5 sunrise pdfs might not be perfect
                    #will check furtther. Looking for better break conditions as I work through this for all pdfs.
                    if "total" in lines[index].lower():
                        break

                    list = lines[index].split()
                    #Get rid of commas 
                    list[-1] = list[-1].replace(",", "")
                   
                   
                   #If it follows desired decimal format 
                    if(re.search(patternDec, list[-1]) and list[-1] != "0.00"):
                        print(list)
                        row[4] = list[-1]  #ext cost
                        row[3] = list[-4] #MSRP (Retail Price)
                        
                        #Get rid of %
                        lines[index-1] = lines[index-1].replace("%", "")
                    
                        #Move to previous element to get Item number and quantity
                        list = lines[index-1].split()
                        row[1] = list[0] #Item Number

                        if(len(list) > 2): #If quantity exists
                            row[2] = list[2] #Extract Quantity Ordered

                        df.loc[len(df)] = row #append to dataframe

                        #Reset row
                        row = ['100',  'Nan', '0', '0', '0', 'Sunrise']
                    index+=1
        #Ignore zeroes
        df = df[df['Ext Price'] != "0.00"]

        self.write_csv(df, fname.strip(".pdf"))

        return df

    def scan_name(self, fname):
        with pdfplumber.open(fname) as pdf:
            print(fname)
            for page in pdf.pages:
                lines = page.extract_text()
                if "quantum" in lines.lower():
                   return self.read_quantum_pdf(fname)
                if "tilite" in lines.lower():
                    return self.read_tilite_pdf(fname)
                if "sunrise" in lines.lower():
                    return self.read_sunrise_pdf(fname)



if __name__ == "__main__":

    columns = ['QuoteID', 'Item Number', 'Qty', 'MSRP', 'Ext Price', 'Vendor']
        
      
    all_df = pd.DataFrame(columns=columns)

    reader = PDF_READER()
    list_of_pdf_filenames = glob.glob('*pdf')

    for  fname in list_of_pdf_filenames:
        all_df = pd.concat([all_df,reader.scan_name(fname)])
    
    reader.write_csv(all_df, "EveryPDF")


   