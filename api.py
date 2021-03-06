import requests, json
import xml.etree.ElementTree as ET

"""
Gets all the drugs being taken by the patient and returns it as a list
"""
def get_drug(firstName, lastName):
    headers = {'Accept': 'application/json'}
    req = requests.get("https://open-ic.epic.com/FHIR/api/FHIR/DSTU2/Patient?family=" + lastName + "&given=" + firstName, headers=headers)

    # need to find a more reliable way
    beginIndex = req.text.find("id") + 5
    endIndex = req.text.find("care") - 3
    token = req.text[beginIndex:endIndex]

    response = requests.get("https://open-ic.epic.com/FHIR/api/FHIR/DSTU2/MedicationOrder?patient=" + token, headers=headers)

    json_data = json.loads(response.text)

    array = json_data["entry"]

    meds = []

    # gets all the drugs and puts them into a list
    for entries in array:
        meds.append(entries["resource"]["medicationReference"]["display"])

    return meds

"""
Gets the RXNormId based on the colloquial name of the drug. If this doesn't exist,
then it returns 0
"""
def get_normid(drug):
    headers = {'Accept': 'application/json'}
    req = requests.get('https://rxnav.nlm.nih.gov/REST/rxcui?name=' + drug, headers)

    root = ET.fromstring(req.text)
    # makes the check that the rxnormId exists
    try:
        normId = root[0][1].text
    except IndexError:
        normId = 00000

    return normId

"""
Returns a description of the interactions between each drug being taken by the
patient and the drug the doctor wants to prescribe. Any drug that does not have
this information is not included. The description is sent as a dictionary with
the key as which drugs are being looked at and the effect as the value
"""
def get_danger(drugs):
    headers = {'Accept': 'application/json'}
    des = {}
    for i in range(0, len(drugs) - 1):
        check_drug = drugs[len(drugs) - 1]
        drug = drugs[i]

        normOne = get_normid(drug) #normId of drug to check
        normTwo = get_normid(check_drug) #normId of drug to be compared to
        # make sure normIds exist
        if (normOne is not 0 and normTwo is not 0):
            req = requests.get('https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis=' + normOne + '+' + normTwo, headers)

            response = req.json()
            description = ''

            # makes sure not to include drugs that don't have the information
            if 'fullInteractionTypeGroup' in response:

                interaction = response['fullInteractionTypeGroup'][0]['fullInteractionType']

                interactionPair = interaction[0]['interactionPair'][0]

                description = interactionPair['description']

                des[drug.capitalize() + ' and ' + check_drug.capitalize()] = description

    return des

"""
Gets the lexographical number for the medication that is passed in
"""
def numbers(medication):
    base_url = "http://184.73.124.73:80/PortalWebService/api/v2/product/allergenIT/search"
    headers = {
        'Authorization': "Basic MTdlYmU3MjQzNGE4NDAzOWEwZTQ4OTAwMThiNmM5OTczZTlBQUMyODk4Q0FCMTE5Qjc5RTk5NDQ4OTcwRkM1QTA4NzI5RDE2OEU3MjQ5N0MwOTE2NjhBOEI1Q0JBNkY3NEU=",
        'Content-Type' : 'application/json',
        'Accept': 'application/json'
    }

    theMedication = medication

    body = {
        "searchTerm": theMedication,
        "numberOfResults": 20,
        "dymSize": 0,
        "page": 1,
        "filterByPrecedence": 1,
        "filterByExpression": "",
        "distinctBy": "",
        "properties": "",
        "showFields": "",
        "clientApp": "AMIA Application",
        "clientAppVersion": "1.0",
        "siteId": "Hopspital ABC",
        "userId": "Admin"
    }

    r = requests.post(base_url, headers=headers, json=body)
    code = r.json()["SearchTermResponse"]["items"][0]["code"]

    return code

"""
Gets the colloquial names of all the drugs only without their chemical names
"""
def get_drug_name(drugs):
    names = []
    for d in drugs:
        n = ''
        if ',' in d:
            n = d[d.index('(') + 1:d.index(',')]
        else:
            n = d[d.index('(') + 1:d.index(')')]
            if ' ' in n:
                n = n[0: n.index(' ')]
        names.append(n)

    return names
