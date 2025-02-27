from lxml import etree
from datetime import datetime
import json

path = "./input.xml"
date_format = "%d/%m/%Y"

ALLOWED_LANGUAGES = {"en", "fr", "de", "es"}
ALLOWED_CURRENCY = ["EUR", "USD", "GBP"]
ALLOWED_NATIONALITIES = ["US", "GB", "CA"]
ALLOWED_MARKETS = ["US", "GB", "CA", "ES"]
ALLOWED_ROOM_COUNT = 10
ALLOWED_ROOM_GUEST_COUNT = 10
ALLOWED_CHILD_COUNT = 4
ALLOWED_HOTEL_COUNT = 10
Time_Format = "%d/%m/%Y"
EXCHANGE_RATES = {
    'USD': {'USD': 1,
           'EUR': 0.96,
           'GBP': 0.79},
    'EUR': {'USD': 1.04,
           'EUR': 1,
           'GBP': 0.83},
    'GBP': {'USD': 1.26,
           'EUR': 1.21,
           'GBP': 1}
}

def validate_value(com_obj, valid_values, default_val, msg):
    """
    Validate different parameter against allowed values and assigning default,
    if not provided and raising exception is not provided currect value.
    Args:
        com_obj(compare object): xml tag
        valid_values: list of pre-defined valid values
        default_val: default value is tag not provided in xml
        msg: type of value that you want to comapre.
    """
    if (com_obj is not None) and (com_obj.text in valid_values):
        com_obj = com_obj.text
    elif com_obj is None:
        com_obj = default_val
    else:
        raise Exception(f"Please provide a valid {msg}")
    return com_obj

def validate_options_quota(xml_obj):
    """
    This function is used to validate options quota.
    """
    options_quota = xml_obj.find("optionsQuota").text
    if options_quota and options_quota.isdigit() and int(options_quota) <= 50:
        pass
    elif not options_quota:
        options_quota = 20
    else:
        raise Exception("OptionsQuota must be integer and less then 50")
    return options_quota

def validate_search_type(xml_obj):
    """
    This function is used to validate search type.
    """
    search_type = xml_obj.find("SearchType").text
    AvailDestinations = ''
    if search_type == "single":
        pass
    elif search_type == "Multiple":
        AvailDestinations = []
    return AvailDestinations

def validate_stay_dates(tree):
    """
    This function is used to validate date. the minimum trip duration should be 3 days and the trip start date should be no less than 2 days from today.
    """
    curr = datetime.now().date()
    start_date = datetime.strptime(tree.find("StartDate").text, Time_Format).date()
    end_date = datetime.strptime(tree.find("EndDate").text, Time_Format).date()
    if (start_date-curr).days < 2:
        raise Exception("start date must be atleast 2 days from now")
    elif (end_date-start_date).days < 3:
        raise Exception("trip must be atleast 3 days")
    return start_date, end_date


def validate_xml(xml_path):
    """
    Function responsible to load the xml, parse, validate the variables and provide the response.
    __define_ocg__
    """
    try:
        # Reading xml file
        tree = etree.parse(xml_path)

        # validating all parameters based on rules
        var_filters_cg = tree.find("source").find("languageCode")
        var_filters_cg = validate_value(var_filters_cg, ALLOWED_LANGUAGES, 'en', 'language')

        options_quota = validate_options_quota(tree)
        var_ocg = tree.find("Configuration").find("Parameters").find("Parameter")
        username = var_ocg.get("username")
        password = var_ocg.get("password")
        company_id = var_ocg.get("CompanyID")
        if not password:
            raise Exception("password is missing")
        elif not username:
            raise Exception("missing username")
        elif not company_id:
            raise Exception("company id is missing")
        elif not company_id.isdigit():
            raise Exception("company id should be integer")

        search_type = validate_search_type(tree)
        start_date, end_date = validate_stay_dates(tree)

        currency = tree.find("Currency")
        currency = validate_value(currency, ALLOWED_CURRENCY, 'EUR', 'currency')

        nationality = tree.find("Nationality")
        nationality = validate_value(nationality, ALLOWED_NATIONALITIES, 'US', 'nationality')

        market = tree.find("Markets")
        market = validate_value(market, ALLOWED_MARKETS, 'ES', 'market')

        rooms_requested = tree.findall('Paxes')
        if len(rooms_requested) > ALLOWED_ROOM_COUNT:
            print("Requested number of rooms exceeds max allowed rooms")
        for room in rooms_requested:
            adults = 0
            child = 0
            persons = room.findall('pax')
            if len(persons) > ALLOWED_ROOM_GUEST_COUNT:
                raise Exception("Number of guest in a room exceeds then the allowed number of guests")
            for person in persons:
                if int(person.get('age')) > 5:
                    adults += 1
                else:
                    child += 1
            if child > ALLOWED_CHILD_COUNT:
                raise Exception("Number of childerns in a room exceeds then the allowed number of childerns")
            if child != 0 and adults == 0:
                raise Exception("An adult must be acompaning the child")
            
            # forming the response once evrything is validated.
            price = {}
            price["minimumSellingPrice"] = None
            price["currency"] = currency
            price["net"] = 132.42
            price["markup"] = 3.2
            price["selling_currency"] = 'USD'
            if price['selling_currency'] == currency:
                price['exchange_rate'] = 1
            else:
                price['exchange_rate'] = EXCHANGE_RATES[price['selling_currency']][currency]
                price['net'] *= price['exchange_rate']
            price['selling_price'] = price['net'] + round(price['net'] * price['markup']/100 ,2)

            response = {}
            response['id'] = 'A#1'
            response["hotelCodeSupplier"] = "39971881"
            response["market"] = market
            response['price'] = price
            return json.dumps(response)
    except Exception as e:
        print(e)
        return e.args[0]

print(validate_xml(path))
