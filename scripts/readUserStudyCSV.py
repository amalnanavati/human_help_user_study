import csv, pprint

def processSurveyData(filepath):
    # Columns from the CSV
    uuidCol = 1
    nasaTLXCols = {
        "Mental Demand": 2,
        "Physical Demand": 3,
        "Temporal Demand": 4,
        "Performance": 5,
        "Effort": 6,
        "Frustration": 7,
    }
    rosasCols = {
        "Competence" : range(8,14),
        "Warmth" : range(14,21),
        "Discomfort" : range(21,27),
        "Curiosity" : range(27,29),
    }
    openEndedCols = {
        "In instances when the robot asked for help, why did you help or not help it?" : 29,
        "In what scenarios would it be acceptable for a real-world robot to ask people for help?" : 30,
        "Did you think the robot was curious? Why or why not?" : 31,
        "Is there anything else you would like us to know?" : 32,
    }
    demographicCols = {
        "Prosociality" : range(33,49),
        "Navigational Ability" : range(49,56),
        "Video Game Experience" : 56,
        "Age" : 57,
        "Gender" : 58,
    }
    # Likert Scale Mappings
    rosasMapping = {
        "Definitely unassociated" : 1,
        "Moderately unassociated" : 2,
        "Neutral" : 3,
        "Moderately associated" : 4,
        "Definitely associated" : 5,
    }
    prosocialityMapping = {
        "Never / Almost Never True" : 1,
        "Occasionally True" : 2,
        "Sometimes True" : 3,
        "Often True" : 4,
        "Always / Almost Always True" : 5,
    }
    navigationalAbilityMapping = {
        "Not applicable to me" : 1,
        "Seldom applicable to me" : 2,
        "Sometimes applicable to me" : 3,
        "Often applicable to me" : 4,
        "Totally applicable to me" : 5,
    }

    processedData = {}

    with open(filepath, "r") as f:
        reader = csv.reader(f)
        header = None
        for row in reader:
            if header is None:
                header = row
                continue
            uuid = int(row[uuidCol])
            if uuid in processedData:
                raise Exception("UUID %d has multiple rows" % uuid)
            processedData[uuid] = {
                "NASA-TLX" : {},
                "RoSAS" : {},
                "Demography" : {},
            }
            for nasaTLXHeading in nasaTLXCols:
                processedData[uuid]["NASA-TLX"][nasaTLXHeading] = int(row[nasaTLXCols[nasaTLXHeading]])
            for rosasHeading in rosasCols:
                total, num = 0, 0
                for col in rosasCols[rosasHeading]:
                    total += rosasMapping[row[col]]
                    num += 1
                processedData[uuid]["RoSAS"][rosasHeading] = total/num
            for openEndedQ, openEndedCol in openEndedCols.items():
                processedData[uuid][openEndedQ] = row[openEndedCol]
            for demographicHeading, demographicCol in demographicCols.items():
                if demographicHeading == "Prosociality":
                    total, num = 0, 0
                    for col in demographicCol:
                        total += prosocialityMapping[row[col]]
                        num += 1
                    processedData[uuid]["Demography"][demographicHeading] = total/num
                elif demographicHeading == "Navigational Ability":
                    total, num = 0, 0
                    for col in demographicCol:
                        total += navigationalAbilityMapping[row[col]]
                        num += 1
                    processedData[uuid]["Demography"][demographicHeading] = total/num
                else:
                    try:
                        val = int(row[demographicCol])
                    except:
                        val = row[demographicCol]
                    processedData[uuid]["Demography"][demographicHeading] = val

    return processedData

if __name__ == "__main__":
    surveyData = processSurveyData("../flask/ec2_outputs/Human Help User Study Survey (Responses) - Form Responses 1.csv")
    pprint.pprint(surveyData)
