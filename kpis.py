import pandas as pd
import math
import plotly.express as px

class KPIS:
    def criticalIncidents(self, dataframe):
        filter = (dataframe["priority"] == "Crítica");
        filteredDf = dataframe[filter];
        return filteredDf.shape[0];
    
    def totalIncidents(self, dataframe):
        return dataframe.shape[0];
    
    def fractionIncidents(self, dataframe):
        counts = dataframe["priority"].value_counts();
        return px.pie(dataframe, values = counts.tolist(), names = counts.index.tolist());
    
    def backlogPriority(self, dataframe):
        # @todo DOES NOT MATCH PDF, criteria is different
        # filter = dataframe[(dataframe["incident status"] != "Closed") & (dataframe["incident status"] != "Resolved")];
        filteredDf = dataframe.query('`incident status` != "Closed" & `incident status` != "Resolved"');
        counts = filteredDf["priority"].value_counts();
        # print(counts);
        return px.pie(filteredDf, values = counts.tolist(), names = counts.index.tolist());
    
    def incidentTypeBreakdown(self, dataframe):
        counts = dataframe["inc type"].value_counts();
        return px.pie(dataframe, values = counts.tolist(), names = counts.index.tolist());
    
    def criticalMeetsSLA(self, dataframe):
        maxSLAHours = 4;
        filter = (dataframe["priority"] == "Crítica");
        filteredDf = dataframe[filter];
        
        filteredDf["create date-time"] = pd.to_datetime(filteredDf["create date-time"], format = "%d/%m/%Y %H:%M");
        filteredDf["resolution date-time"] = pd.to_datetime(filteredDf["resolution date-time"], format = "%d/%m/%Y %H:%M");

        filteredDf["SLATime"] = (filteredDf["resolution date-time"] - filteredDf["create date-time"]).dt.seconds;
        
        # @note https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
        timeSum = filteredDf["SLATime"].sum(axis = 0);
        meetsSLA = 0;
        meetsSLATime = [];
        doesNotMeetSLA = 0;
        doesNotMeetSLATime = [];
        for index, row in filteredDf.iterrows():
            # @note This is in seconds so we compare to seconds
            if (row["SLATime"] <= (maxSLAHours * 60 * 60)):
                meetsSLA += 1;
                meetsSLATime.append(row["SLATime"]);
            else:
                doesNotMeetSLA += 1;
                doesNotMeetSLATime.append(row["SLATime"]);

        if len(meetsSLATime) > 0:
            meetsSLATime = sum(meetsSLATime) / len(meetsSLATime);
            # @note To hours as float
            meetsSLATime = (meetsSLATime / 60) / 60;
            meetsSLATimeMinsRem = float(meetsSLATime) - math.floor(meetsSLATime);
            meetsSLATimeMinsRem = meetsSLATimeMinsRem * 60;
            finalMeetsSLAString = str(math.floor(meetsSLATime)) + " hours and " + str(round(meetsSLATimeMinsRem)) + " minutes";
        else:
            finalMeetsSLAString = "No incidents to report under these conditions";
        
        if len(doesNotMeetSLATime) > 0:
            doesNotMeetSLATime = sum(doesNotMeetSLATime) / len(doesNotMeetSLATime);
            # @note To hours as float
            doesNotMeetSLATime = (doesNotMeetSLATime / 60) / 60;
            doesNotMeetSLATimeMinsRem = float(doesNotMeetSLATime) - math.floor(doesNotMeetSLATime);
            doesNotMeetSLATimeMinsRem = doesNotMeetSLATimeMinsRem * 60;
            finalDoesNotMeetSLAString = str(math.floor(doesNotMeetSLATime)) + " hours and " + str(round(doesNotMeetSLATimeMinsRem)) + " minutes";
        else:
            finalDoesNotMeetSLAString = "No incidents to report under these conditions";
            
        return {"chart": px.pie(dataframe, values = [meetsSLA, doesNotMeetSLA], names = ["Meets SLA", "Does NOT meet SLA"]), "timings": {"meets": finalMeetsSLAString, "doesnot": finalDoesNotMeetSLAString}};
    
    def custom(self, dataframe):
        counts = dataframe["incident status"].value_counts(dropna = False);
        return px.pie(dataframe, values = counts.tolist(), names = counts.index.tolist());