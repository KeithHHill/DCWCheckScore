import os
import database
import datetime
import ConfigParser
from os.path import join as pjoin
import sendEmail

db = database.Database()
path = os.path.dirname(os.path.abspath(__file__))

#pull configs from a config file
config = ConfigParser.ConfigParser()
config.read(path + "/config.ini")
filepath = config.get('data','file_location')
scoreThreshold = int(config.get('data','score_threshold'))
rosterThreshold = int(config.get('data','roster_threshold'))
rosterUpdateIsRunning = False

#get the most recent event to make sure one is ongoing for at least 3 hours
mostRecentEvents = db.fetchAll("""
    select *
    from events 
    where start_date < date_sub(now(), interval 3 hour)
    and end_date > now()
    order by start_date desc limit 1
    """)




if len(mostRecentEvents) > 0 :
    for mostRecentEvent in mostRecentEvents :
        # check if a roster update is running
        lastRuns = db.fetchAll("""select *, TIMEDIFF(now(),start_time) as time_since_last_run 
                                    from script_runs 
                                    where message is null
                                    and ((script in("activities_threaded instance_1","updateClanMembers_update", "carnage_threaded instance_1")
                                    and records > 0) or script in("updateClanMembers_update")) 
                                    order by start_time desc
                                    limit 3"""
                              )
        for lastRun in lastRuns :
            if str(lastRun["script"]) == "updateClanMembers_update" :
                rosterUpdateIsRunning = True
                timeSinceLastRun = datetime.datetime.strptime(str(lastRun["time_since_last_run"]),'%H:%M:%S.%f')
        
        lastScript = str(lastRuns[0]["script"])

        if not rosterUpdateIsRunning :
            # get the most recent score update record since roster isn't updating
            lastRuns = db.fetchAll("""select max(sub.start_time) as last_updated, TIMEDIFF(now(),max(sub.start_time)) as time_since_last_update from
                (
                (select act_start_time as start_time from score_update_progress where act_pull_progress > 0 order by id desc limit 1)
                union
                (select carnage_start_time as start_time from score_update_progress where act_pull_progress > 0 order by id desc limit 1)
                ) sub""")
            timeSinceLastRun = datetime.datetime.strptime(str(lastRuns[0]["time_since_last_update"]),'%H:%M:%S')

        db.close();

        minutesSinceLastRun = (timeSinceLastRun.hour * 60) + timeSinceLastRun.minute
        
 

        # if the last update was too long ago, write to a file (IFTTT will generate an email)
        if (rosterUpdateIsRunning and minutesSinceLastRun > rosterThreshold) :
            # fout = open(filepath + "_" + "updateClanMembers_update_" + str(minutesSinceLastRun) + "min.txt", "w")
            msg = "\r\n".join([
              "From: noreply@destinyclanwars.com",
              "To: noreply@destinyclanwars.com",
              "Subject: WARNING: DCW may have stopped",
              "",
              "WARNING: The roster refresh is currently running and has not completed in " + str(minutesSinceLastRun) + " minutes and is beyond the configured threshold."
              ])
            sendEmail.sendMessage(msg)

        elif (rosterUpdateIsRunning == False and minutesSinceLastRun > scoreThreshold) :
            # fout = open(filepath + "_" + lastScript + "_" + str(minutesSinceLastRun) + "min.txt", "w")
            msg = "\r\n".join([
              "From: noreply@destinyclanwars.com",
              "To: noreply@destinyclanwars.com",
              "Subject: WARNING: DCW may have stopped",
              "",
              "WARNING: The roster refresh is currently running and has not completed in " + str(minutesSinceLastRun) + " minutes and is beyond the configured threshold."
              ])
            sendEmail.sendMessage(msg)