#!/usr/bin/env python
# coding: utf-8

# # Meyer Packard Algorithm-Utkarsh Pratap Singh 17MT10043

# In[1]:


#importing necessary libraries
import numpy
import random
import operator
from bs4 import BeautifulSoup as bs
import urllib.request  as urllib2 
import csv


# In[7]:


#Now setting up the population size, number of generations for which the code shall be running, rate of mutation in chromosomes, 
#name of the stock in the form of firm’s ticker, NumReturn to return best possible number of chromosomes, 
#number of days of the traded stock which is by default kept as a year
random.seed(a=None)
# Set the Constants ---------------
PopulationSize = 200
DataSize = 0
NumberOfGenerations = 4
MutationRate = 5
MutationChange = 2
Stock_name = 'race' #set the firm ticker that we want to anaylse(use RACE for ferrari and TSLA for tesla) 
NumReturn = 5
NumberOfDay = 365
File_path = '2Improvement.csv'#results will be saved in this 


# In[8]:


pwd #check the directory


# In[9]:


#chromosomes are the most granular fighting or competing entities
#Min is the minimum score(fitness) of chromosomes and max is the maximum. 
#Before the addition of a new chromosome in the set it would have a previous maximum and minimum. 
#Buy denotes the buying or longing tendency of the stocks by the user and lastly score denotes the fitness score of the chromosome.

class Chromosome():
    def __init__(self, min=None, max=None, prev_min=None, prev_max=None, buy=None, score =None):
        self.min = min
        self.max = max
        self.prev_min = prev_min
        self.prev_max = prev_max
        self.buy = buy
        self.score = score
#defining funtion to mutate the chromosomes 
#Mutation is done by introducing toChange variable, which will mutate a maximum of 5 chromosomes
#in an iteration with mean and standard distribution as 0,0.15 respectively
    def mutate(self):
        mu, sigma = 0, 0.15 # mean and standard deviation
        s = numpy.random.normal(mu, sigma, 1)#edit-1
        x = iter(s)
        toChange = random.randint(0,5)
        if toChange == 0:
           self.buy = random.randint(0,999)%2
        if toChange == 1:
            self.min = next(x)
        if toChange == 2:
            self.max = next(x)
        if toChange == 3:
            self.prev_min = next(x)
        if toChange == 4:
            self.prev_max = next(x)
        if self.min > self.max:
            self.min, self.max = self.max, self.min
        if self.prev_min > self.prev_max:
            self.prev_min, self.prev_max = self.prev_max, self.prev_min
#To generate training data and train the algorithm
#Lists of population, next generation chromosomes, dayChange for the price change of a stock on a day 
#and next day change is change on the very next day, profit is the positive change incurred while buying 
#the stocks if the change is positively increasing day to day. 

class TrainingData(object):
    population = []
    nextGeneration = []
    dayChange = []
    nextDayChange = []
    profit = []

    def __init__(self, stockName = '', popSize = None, mRate = None, mChange = None):
        self.stockName = stockName
        self.popSize= popSize
        self.mRate = mRate
        self.mChange= mChange

#Generate Data from chosen stock
#Here in the below code, the following generates the data from yahoo finance to be specific
#and leaves behind the dividend column for the analysis
    def generateData(self):
        global DataSize
        
        #Download the data from yahoo finance for last 365 days
        data = []
        url = "https://finance.yahoo.com/quote/" + Stock_name + "/history/"
        rows = bs(urllib2.urlopen(url).read(), "lxml").findAll('table')[0].tbody.findAll('tr')
        
        for each_row in rows:
            divs = each_row.findAll('td')
            if divs[1].span.text  != 'Dividend': #Ignore this row in the table
                #I'm only interested in 'Open' price; For other values, play with divs[1 - 5]
                data.append({'open': divs[1].span.text, 'Adj close': float(divs[5].span.text.replace(',',''))})
        data[:NumberOfDay]
        print(data)
        
        file = open('stock_data', 'w')
        closes = [c['Adj close'] for c in data]
        opens = [o['open'] for o in data]
        oArray = []
        cArray = []

        for c in closes:
            cArray.append(c)

        for o in opens:
            oArray.append(o)

        for x in range(len(data)-2):
            #  %Difference, Next Day %Difference, Money Made Holding for a Day
            file.write(str((float(cArray[x])-float(oArray[x+1]))/100) + ' ' + str((float(cArray[x+1]) - float(oArray[x+2]))/100) + ' ' + str((float(oArray[x]) - float(oArray[x+1]))) + '\n')

            self.dayChange.append((float(cArray[x])-float(oArray[x+1]))/100)
            self.nextDayChange.append((float(cArray[x+1]) - float(oArray[x+2]))/100)
            self.profit.append(float(oArray[x]) - float(oArray[x+1]))
        #Makes sure the population size is
        DataSize = len(self.dayChange)
        file.close()

#Initializes the population of random chromosomes
#The population of the chromosomes are from a random uniform normal distribution with mean 0 and standard deviation 0.15. 
#Given the code above, initializes the population
    def populationInit(self):

        #Create N Chromosomes with N being the Population Size
        #Each variable of Chromosome is assigned a number from a normal distribution
        #with the mean being 0 and the Standard Deviation being 1.5

        mu, sigma = 0, 0.15 # mean and standard deviation
        s = numpy.random.normal(mu, sigma, 4*PopulationSize)
        x = iter(s)
        for i in range(PopulationSize):
            temp = Chromosome(next(x),next(x),next(x),next(x),random.randint(0,999)%2, 0)

            #If the mininum is assigned a higher value than the max swap them
            #so that it makes sense.
            if temp.min > temp.max:
                temp.min, temp.max = temp.max, temp.min
            if temp.prev_min > temp.prev_max:
                temp.prev_min, temp.prev_max = temp.prev_max, temp.prev_min

            #Push the Chromosome into the population array.
            self.population.append(temp)

    #Determines score for each chromosome in self.population
#The difficult task was to decide what could be the fitness function or the score, 
#is calculated such as the change in present day prices is more than the previous minimum, 
#present day change is less than previous maximum also if the next day change is more than minimum and less than maximum of present day.
#So, if these conditions satisfy and if the buy has its value equal to 1, then it would add profit into the score otherwise subtract 
#from it and if neither of these cases meet then the score is given as -5000 to start with.
    def fitnessFunction(self):
        for i in range(len(self.population)):
            match = False
            for j in range(DataSize):

                #print(self.population[i].min, self.nextDayChange[j], self.population[i].max)
                #If match is found we BUY
                if(self.population[i].prev_min < self.dayChange[j] and self.population[i].prev_max > self.dayChange[j]):
                    if(self.population[i].min < self.nextDayChange[j] and self.population[i].max > self.nextDayChange[j]):
                        if(self.population[i].buy == 1):
                            match = True
                            self.population[i].score += self.profit[j]

                #Match is found and we short
                if(self.population[i].prev_min < self.dayChange[j] and self.population[i].prev_max > self.dayChange[j]):
                    if(self.population[i].min < self.nextDayChange[j] and self.population[i].max > self.nextDayChange[j]):
                        if(self.population[i].buy == 0):
                            match = True
                            self.population[i].score -= self.profit[j]

                #We have not found any matches = -5000
                if match == False:
                    self.population[i].score = -5000
            #print(self.population[i].score)

    #Weighted random choice selection
#The above function calculates the fitness value of a population and then randomly selects a value(pick) from uniform range of (0,max(score)),
#where max(score is the score of the total chromosomes combined in the population and in the next loop it selects a population’s score and adds
#it to variable ‘current’ and if currency exceeds the ‘pick’, then we go onto the next generation and append the current population in the nextGeneration[ ]

    def weighted_random_choice(self):
        self.fitnessFunction()
        max = self.population[0].score
        for i in self.population[1:]:
            max+= i.score
        pick = random.uniform(0,max)
        current = 0
        for i in range(len(self.population)):
            current += self.population[i].score
            if current > pick:
                self.nextGeneration.append(self.population[i])

    #Removes the indices in self.population that have a score of None
    def exists(self):
        i = 0
        while i <len(self.population):
            if self.population[i].score is None:
                del self.population[i]
            else:
                i+=1

    #Uniform Crossover
#The below function performs Uniform crossover in the current population and swaps if the child has a better score than the previous minimum.
    def uniformCross(self, z):
        children = []
        for i in range(PopulationSize-len(self.nextGeneration)):
            child = Chromosome(0,0,0,0,0)
            chromosome1 = self.nextGeneration[random.randint(0,999999) % len(self.nextGeneration)]
            chromosome2 = self.nextGeneration[random.randint(0,999999) % len(self.nextGeneration)]
            if(random.randint(0,999) %2):
                child.min = chromosome1.min
            else:
                child.min = chromosome2.min

            if(random.randint(0,999) %2):
                child.max = chromosome1.max

            else:
                child.max = chromosome2.max

            #Check to make sure the swap yields viable chromosome
            if child.max < child.min:
                    child.max, child.min = child.min, child.max

            if(random.randint(0,999) %2):
                child.prev_min = chromosome1.prev_min
            else:
                child.prev_min = chromosome2.prev_min

            if(random.randint(0,999) %2):
                child.prev_max = chromosome1.prev_max
            else:
                child.prev_max = chromosome2.prev_max

            #Check if swap is needed
            if child.prev_max < child.prev_min:
                    child.prev_max, child.prev_min = child.prev_min, child.prev_max

            if(random.randint(0,999) %2):
                child.buy = chromosome1.buy
            else:
                child.buy = chromosome2.buy

            #Append
            children.append(child)

        #Mutation
	#Performing mutation in the population randomly and the child is added in the population, and after performing competition 
	#on the basis of fitness function the required number of population is kept in the next generation and then the population’s 
	#chromosomes are sorted on the basis of their scores.
        for i in range(len(children)):
            if random.randint(0,999) % 100 <= z:
                children[i].mutate()
        self.population[i] = children[i]
        for i in range(len(children),len(self.population),1):
            self.population[i] = self.nextGeneration[i-len(children)]
        self.exists()
        self.fitnessFunction()
        self.population.sort(key=operator.attrgetter('score'))

    #Print the scores of the chromosomes
#The print chromosomes function prints all the chromosomes and along with selects the top NumReturn values from it because 
#they are already sorted according to their scores.
#And gives suggestions whether to long(buy) the stock or to short(sell) it.

    def printChromosomes(self):
        buyRec = []
        shortRec = []
        for i in range(len(self.population)):
            if(self.population[i].buy == 1):
                buyRec.append(self.population[i])
            if(self.population[i].buy == 0):
                shortRec.append(self.population[i])

        print("The Best %d Chromosomes When Buying" % (NumReturn))
        outputBuy = []
        outputShort = []
        fieldnames = ["Score"]
        i = 1
        size = len(buyRec)
        while i < NumReturn + 1:
            index = size - i
            print("min: %f  | max: %f  | previous min: %f  | previous max: %f  |  score: %f" % (buyRec[index].min, buyRec[index].max, buyRec[index].prev_min, buyRec[index].prev_max, buyRec[index].score))
            outputBuy.append(buyRec[index].score)
            i += 1
        print("The Best %d Chromosomes When Shorting" % (NumReturn))
        i = 1
        size = len(shortRec)
        while i < NumReturn+1:
            index = size-i
            print("min: %f  | max: %f  | previous min: %f  | previous max: %f  |  score: %f" % (shortRec[index].min, shortRec[index].max, shortRec[index].prev_min, shortRec[index].prev_max, shortRec[index].score))
            outputShort.append(shortRec[index].score)
            i+=1
        #print("Todays Stats")
        print('output scores when we buy today',outputBuy)
        print('output scores when we short today',outputShort)
        my_list = []
        for i  in range(len(outputBuy)):
            if outputBuy[i]>outputShort[i]:
                my_list.append(1)
            else: my_list.append(0)
        avg=sum(my_list)/len(my_list)
        print(my_list)
        if avg>=0.5:
            print('Buy the Stock')
        else:
            print('Short/Sell the Stock')
        #print(fieldnames)
        #for i in range(len(self.population)):
            #inner_dict = dict(zip(fieldnames, i))
            #my_list.append(inner_dict)
        #print(inner_dict)    
        #x.csv_dict_writer(File_path,fieldnames,my_list)
       
        
    #def csv_dict_writer(path, fieldnames, data):
        #out_file  = open(path, "wb")
        #writer = csv.DictWriter(out_file, delimiter=',', fieldnames=fieldnames)
        #writer.writeheader()
        #for row in data:
            #writer.writerow(row)
        #out_file.close()

if __name__ == '__main__':
    x = TrainingData()
    x.generateData()
    x.populationInit()
    x.weighted_random_choice()
    x.uniformCross(MutationRate)
    x.printChromosomes()


# In[11]:


#function to get historical data for a number of days for a given stock
def get_historical_data(name, number_of_days):
	data = []
	url = "https://finance.yahoo.com/quote/" + name + "/history/"
	rows = bs(urllib2.urlopen(url).read(), "lxml").findAll('table')[0].tbody.findAll('tr')

	for each_row in rows:
		divs = each_row.findAll('td')
		if divs[1].span.text != 'Dividend': #Ignore this row in the table
			#I'm only interested in 'Open' price; For other values, play with divs[1 - 5]
			data.append({'Date': divs[0].span.text, 'Adj close': float(divs[1].span.text.replace(',',''))})
#data.append({'open': divs[1].span.text, 'Adj close': float(divs[5].span.text.replace(',',''))})
	return data[:number_of_days]

#Test
print (get_historical_data('race', 15))


# Check for tesla and ferrari for 19 days(Don't run the cell further)

# In[ ]:

'''
Dates     6th march      7th      8th          9th      10th    11th          12th          13th     14th    15th          16th      17th          18th       19th      20th      21st      22nd         23rd          24th(19th May)
tesla:   -690(long)     605.39   640.2        595      772.28  710.8(Short) 737.61(Long)  795.64   790.17  855.9          755       701           776.5     777.21    793.77    827.0     780.0        790.35        827.78
ferrari: +152.27(short) 141.17   145.89(Long) 143.93   162.89  158(Short)   157.56(Long)  159.53   159     156.37(Short)  153.69    154.26(Long) 158.33     157.89    158.33    160.14    151.2(Short)  157.52(Long) 169.99                    
'''

# In[ ]:




