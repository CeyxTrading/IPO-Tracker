# IPO-Tracker
a tool that tracks IPO price
![image](https://github.com/CeyxTrading/IPO-Tracker/assets/119662508/f33915b1-8bb8-43d9-8dac-4140c1d86887)

I opted to create an IPO price tracking system that automates price updates and monitors price trends. Additionally, I envisioned the tracker dashboard to be presented in HTML format. This choice would enable me to incorporate links to Yahoo Finance for convenient access to information about the company's background, media coverage, and fundamentals.

The implementation involves the following steps:

1. Retrieve a list of IPO companies with IPO dates from Financial Modeling Prep.

2. For each IPO, gather minute-by-minute prices for the past 30 days.

3. Resample the prices at various time intervals (hours, days, weeks) and calculate the price changes for the last four periods within each time interval.

4. For each combination of time interval and period, identify the minimum and maximum percentage change. Translate these values into a color heatmap.

5. Generate a Bootstrap HTML report displaying percentage change values, using hex colors as cell backgrounds in the table.

6. Save the HTML report.

7. Continuously update this report every minute to ensure real-time information.

