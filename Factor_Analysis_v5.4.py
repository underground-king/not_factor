#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 26 17:42:23 2017

@author: Rey
"""
import pandas_datareader as pdr
import datetime 
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from pandas_datareader.data import DataReader

# WHAT IM WORKING ON:
# get model to give outlier dates
# pimp out graphs

# FUTURE IMPROVEMENTS:
# importing a portfolio from excel as underlying
# similar to above to custom make benchmarks





ticker='INXX'
bench='EEM'
fac='XTEITT01INM156N'
fac_2='XTEITT01INM156N'
fred_data=True
complex=False

# complex should be true a factor tested is an excess return (ex. value-growth) and false if it is a stand-alone factor (ex. oil)
start_investment=100
# decides original 'investment' for indexed price chart


period=3

# Used for regression analysis. Defines the number of periods per recorded price move. The length of a period is defined by how often the factor data is recorded. So if we are using a factor that has monthly data, a period of 3 would use tri-monthly price changes in the analysis. If we are not using fred data, we usually pull daily data, so a period of 20 would use intervals of 20 trading days.

period_length='d'
# dont touch this

#valid values are 'd' for daily, 'w' for weekly,
#'m' for monthly and 'v' for dividend.

start_date=datetime.datetime(2010, 9, 19)
end_date=datetime.datetime(2018, 1, 2)

all_dates=pd.DataFrame(pd.date_range(start_date, end_date, freq='D'))
all_dates.columns=['All Dates']
all_dates=all_dates.set_index(all_dates['All Dates'])
# is part of the process that fills in nan values for underlying and benchmark to match factor data values


# choose tickers to analyze and what to scale charts from
print('fetching underlying data...')

underlying = pdr.get_data_yahoo(ticker, 
                          start=start_date, 
                          end=end_date,retry_count=4,interval=period_length)

original_underlying_data_shape=('original number of datapoints(underlying): '+str(len(underlying.index)))

underlying_graph=underlying.copy()


#------------------------------------------------------------------------
if fred_data==True:
    underlying = pd.concat([all_dates[['All Dates']], underlying], axis=1)
    underlying.fillna(method='ffill',inplace=True)
#------------------------------------------------------------------------
# above replaces holiday and weekend NAN stock values with the price on the next available date. This is done to make sure that they allign with when the factor data is available.

print('fetching benchmark data...')

benchmark = pdr.get_data_yahoo(bench, 
                          start=start_date, 
                          end=end_date,retry_count=4,interval=period_length)


benchmark_graph=benchmark.copy()
#------------------------------------------------------------------------
if fred_data==True:
    benchmark = pd.concat([all_dates[['All Dates']], benchmark], axis=1)
    benchmark.fillna(method='ffill',inplace=True)
#------------------------------------------------------------------------
# above replaces holiday and weekend NAN stock values with the price on the next available date. This is done to make sure that they allign with when the factor data is available.



print('fetching factor data...')

if fred_data==False:
    factor = pdr.get_data_yahoo(fac, 
                          start=start_date, 
                          end=end_date,retry_count=4,interval=period_length)
    original_factor_data_shape=('original number of datapoints(factor 1): '+str(len(factor.index)))
elif fred_data==True:
    factor=DataReader(fac, 'fred', start=start_date,end=end_date)
    factor.columns=['Factor Close']
    original_factor_data_shape=('original number of datapoints(factor 1): '+str(len(factor.index)))
    underlying = pd.concat([factor[['Factor Close']], underlying], axis=1)
    underlying=underlying.dropna()
    factor['Close']=underlying['Factor Close']
    factor=factor.dropna()
    benchmark = pd.concat([underlying[['Factor Close']], benchmark], axis=1)
    benchmark=benchmark.dropna()
    


if fred_data==False:
    factor_2 = pdr.get_data_yahoo(fac_2, 
                          start=start_date, 
                          end=end_date,retry_count=4,interval=period_length)
    original_factor2_data_shape=('original number of datapoints(factor 2): '+str(len(factor_2.index)))
elif fred_data==True:
    factor_2=DataReader(fac_2, 'fred', start=start_date,end=end_date)
    factor_2.columns=['Factor 2 Close']
    original_factor2_data_shape=('original number of datapoints(factor 2): '+str(len(factor_2.index)))
    underlying = pd.concat([factor_2[['Factor 2 Close']], underlying], axis=1)
    underlying=underlying.dropna()
    factor_2['Close']=underlying['Factor 2 Close']
    factor_2=factor_2.dropna()
    benchmark = pd.concat([underlying[['Factor 2 Close']], benchmark], axis=1)
    benchmark=benchmark.dropna()
    
print('loading analysis...')

cleansed_underlying_data_shape=('cleansed number of datapoints(underlying): '+str(len(underlying.index)))
cleansed_factor_data_shape=('cleansed number of datapoints(factor 1): '+str(len(factor.index)))
cleansed_factor2_data_shape=('cleansed number of datapoints(factor 2): '+str(len(factor_2.index)))

#calls data 


def scale_close(close_list):
    scale_i=[]
    sti=start_investment
    recent_close=close_list[0]
    for i in close_list:
        percent_change=(i-recent_close)/recent_close
        scaled_close=sti*(1+percent_change)
        recent_close=i
        scale_i.append(scaled_close)
        sti=scaled_close
    return scale_i

# scale_close function turns closing prices into "if x ammount of dollars were to be invested" style return. Allows for comparability
    
def daily_return(close_list):
    daily_returns=[]
    recent_close=close_list[0]
    for i in close_list:
        percent_change=(i-recent_close)/recent_close
        recent_close=i
        daily_returns.append(percent_change)
    return daily_returns
# provides a list with the daily returns of of inputed close list. note that return for day one is '0'. so it has the same number of changes in price and close dates

def periodic_return(close_list):
    periodic_returns=[]
    recent_close=close_list[0]
    count=0
    for i in close_list:
        if count%period==0 and count!=0:
            percent_change=(i-recent_close)/recent_close
            recent_close=i
            periodic_returns.append(percent_change)
            count=count+1
        else:
            count=count+1
    return periodic_returns

# provides a list with the periodic returns of of inputed close list. note that return for period one is '0'. so it has the same number of changes in price and close dates

underlying_scaled_list=pd.Series(scale_close(underlying_graph['Close']))
benchmark_scaled_list=pd.Series(scale_close(benchmark_graph['Close']))
# calls scale_close function on data to create series with the new adjusted quotes


underlying_periodic_returns=pd.Series(periodic_return(underlying['Close']))
benchmark_periodic_returns=pd.Series(periodic_return(benchmark['Close']))
underlying_excess_returns=underlying_periodic_returns-benchmark_periodic_returns
factor_periodic_returns=pd.Series(periodic_return(factor['Close']))
factor_2_periodic_returns=pd.Series(periodic_return(factor_2['Close']))
if complex==True:
    complex_factor_periodic_returns=factor_periodic_returns-factor_2_periodic_returns
elif complex==False:
    complex_factor_periodic_returns=factor_periodic_returns
# creates series with daily returns of assets: uses factor periodic returns when dealing with a simple factor (ex. oil) and complex when dealing with complex (ex. value-growth)
analysis_input_shape=('cleansed number of datapoints(analysis): '+str(len(underlying_excess_returns.index)))


underlying_graph['Scaled Close'] = list(underlying_scaled_list)
benchmark_graph['Scaled Close'] = list(benchmark_scaled_list)



# adds new adjusted quotes to original data dataframes

plt.plot(underlying_graph['Scaled Close'],alpha=.5,c='green',label=ticker,linestyle='solid',linewidth=1.75)
plt.plot(benchmark_graph['Scaled Close'],alpha=.5,c='blue',label=bench,linestyle='solid',linewidth=1.75)


plt.grid(True)
plt.xlabel('Date',fontsize=12)
plt.ylabel('Price (USD)',fontsize=12)
plt.title('Indexed Price Chart',fontsize=14)
plt.axis('tight')
plt.legend(loc='upper left', frameon=False)


plt.show()
# scaled price chart


plt.scatter(complex_factor_periodic_returns,underlying_excess_returns,alpha=.7,c='orange',label=ticker,linestyle='solid',linewidth=1.75)
#use factor periodic returns when dealing with a simple factor (ex. oil) and complex when dealing with complex (ex. value-growth)

if complex==True:
   factor_scatter_x_label='Factor: '+fac+'-'+fac_2
elif complex==False:
    factor_scatter_x_label='Factor: '+fac


ax = plt.axes()
ax.tick_params(colors='gray', direction='out')
plt.grid(True)
plt.xlabel(factor_scatter_x_label,fontsize=12)
plt.ylabel(ticker+' '+str(period)+' day excess return',fontsize=12)
plt.title('Factor Test',fontsize=14)
plt.grid(color='w',linestyle='solid')
plt.axis('tight')

plt.show()
#factor regression chart


underlying_vol=np.std(underlying_periodic_returns)
benchmark_vol=np.std(benchmark_periodic_returns)
regression=sm.OLS(endog=underlying_excess_returns, exog=complex_factor_periodic_returns).fit()
regression_outliers=regression.outlier_test()
regression_outliers=pd.Series(regression_outliers['bonf(p)'])

# use factor periodic returns when dealing with a simple factor (ex. oil) and complex when dealing with complex (ex. value-growth)

# i decided to search for outliers based on outliers in set of residuals instead of outliers from original data. if i did origina data and for example the fix jumped and the underlying dropped, both by large ammounts, they would both be eliminated and that makes no sense. insetad, i identify outliers when the relationship between the excess returns and factor (residual) is an outlier to the other residuals. this can tell us that the price of the underlying changed dramatically because of a firm-specific event rather than anything related with factors. however, it is always reccomended to research what caused outliers.

underlying_excess_returns_without_outliers=underlying_excess_returns[regression_outliers>.9]
complex_factor_periodic_returns_without_outliers=complex_factor_periodic_returns[regression_outliers>.9]

number_of_outliers=(underlying_excess_returns.count())-(underlying_excess_returns_without_outliers.count())
outlier_as_percent_of_data=number_of_outliers/underlying_excess_returns.count()

regression_without_outliers=sm.OLS(endog=underlying_excess_returns_without_outliers, exog=complex_factor_periodic_returns_without_outliers).fit()

plt.scatter(complex_factor_periodic_returns_without_outliers,underlying_excess_returns_without_outliers,alpha=.7,c='blue',label=ticker,linestyle='solid',linewidth=1.75)
#use factor periodic returns when dealing with a simple factor (ex. oil) and complex when dealing with complex (ex. value-growth)

if complex==True:
   factor_scatter_x_label='Factor: '+fac+'-'+fac_2
elif complex==False:
    factor_scatter_x_label='Factor: '+fac


ax = plt.axes()
ax.tick_params(colors='gray', direction='out')
plt.grid(True)
plt.xlabel(factor_scatter_x_label,fontsize=12)
plt.ylabel(ticker+' '+str(period)+' day excess return',fontsize=12)
plt.title('Factor Test (extracted outliers)',fontsize=14)
plt.grid(color='w',linestyle='solid')
plt.axis('tight')

plt.show()

print ('Benchmark: '+bench)
print (ticker+' '+str(period)+' day vol: ' +str(underlying_vol))
print ('Benchmark '+str(period)+' day vol: '+str(benchmark_vol))
print ('Factor being tested: '+fac+'-'+fac_2)
print(' ')
print(' ')
print('---RAW REGRESSION---')
print(' ')
print(regression.summary())
print(' ')
print(' ')
print('---FILTERED REGRESSION---')
print(' ')
print(regression_without_outliers.summary())
print(' ')
print(' ')
print('number of outliers identified: '+str(number_of_outliers))
print('percent of original data identified as outliers: '+str(outlier_as_percent_of_data))
print(' ')
print(' ')
print('---DATA MANIPULATION SUMMARY---')
print('data start date: '+str(start_date))
print('data end date: '+str(end_date))
print('period length: '+str(period)+ '    (up to user to know if data is m,d,q, or y)')
print (original_underlying_data_shape)
print (original_factor_data_shape)
print (original_factor2_data_shape)
print (cleansed_underlying_data_shape)
print (cleansed_factor_data_shape)
print (cleansed_factor2_data_shape)
print(analysis_input_shape)
print('expected number of datapoints used in analysis: '+ str(len(underlying.index)/period))



#issues: all dates where there are NOT both factor and underlying data are deleted. This sometimes deletes a meaningful ammount data (especially when using factor data released monthly). ex. if factor data is released on the 1st of every month, then all data points that had the 1st of the month on a weekend will not be included as there will be no closing price for the underlying.