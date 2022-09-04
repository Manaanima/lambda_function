### Required Libraries ###
from datetime import datetime
from dateutil.relativedelta import relativedelta

### Functionality Helper Functions ###
def parse_int(n):
    """
    Securely converts a non-integer value to integer.
    """
    try:
        return int(n)
    except ValueError:
        return float("nan")


def build_validation_result(is_valid, violated_slot, message_content):
    """
    Define a result message structured as Lex response.
    """
    if message_content is None:
        return {"isValid": is_valid, "violatedSlot": violated_slot}

    return {
        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }

def validate_data(age, investment_amount, intent_request):
    """
    Validates the data provided by the user.
    """
    
    # Validates that the user is older than 0 years old and younger than 65 years old
    if age is not None:
        age = parse_int(
            age
        )
        if age < 0:
            return build_validation_result(
                False,
                "age",
                "This is not a valid age, "
                "please provide a different age.",
            )
        elif age > 65:
            return build_validation_result(
                False,
                "age",
                "Sorry, you are already at retirement age! I cannot recommend a portfolio.",
            )

    # Validates that the investment amount is greater than or equal to 5000
    if investment_amount is not None:
        investment_amount = parse_int(
            investment_amount
        )
        if investment_amount <= 4999:
            return build_validation_result(
                False,
                "investmentAmount",
                "Your investment amount must be greater than or equal to $5000, "
                "please provide a different investment amount.",
            )

    # Returns True if age or amount are validated
    return build_validation_result(True, None, None)

def get_risks(risk_level):
    """
    Retrieves the risk level given by the user
    """
    risk_levels = {
        "none" : "100% bonds (AGG), 0% equities (SPY)",
        "low" : "60% bonds (AGG), 40% equities (SPY)",
        "medium" : "40% bonds (AGG), 60% equities (SPY)",
        "high" : "20% bonds (AGG), 80% equities (SPY)",
    }
    return risk_levels[risk_level]    

### Dialog Actions Helper Functions ###
def get_slots(intent_request):
    """
    Fetch all the slots and their values from the current intent.
    """
    return intent_request["currentIntent"]["slots"]


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Defines an elicit slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "ElicitSlot",
            "intentName": intent_name,
            "slots": slots,
            "slotToElicit": slot_to_elicit,
            "message": message,
        },
    }


def delegate(session_attributes, slots):
    """
    Defines a delegate slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {"type": "Delegate", "slots": slots},
    }


def close(session_attributes, fulfillment_state, message):
    """
    Defines a close slot type response.
    """

    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }

    return response

### Intents Handlers ###
def recommend_portfolio(intent_request):
    """
    Performs dialog management and fulfillment for recommending a portfolio.
    """

    first_name = get_slots(intent_request)["firstName"]
    age = get_slots(intent_request)["age"]
    investment_amount = get_slots(intent_request)["investmentAmount"]
    risk_level = get_slots(intent_request)["riskLevel"]
    source = intent_request["invocationSource"]

    # Gets the invocation source
    source = intent_request["invocationSource"]

    if source == "DialogCodeHook":

        # Gets all the slots
        slots = get_slots(intent_request)

        # Validates user's input using the validate_data function
        validation_result = validate_data(age, investment_amount, intent_request)

        # Uses elicitSlot dialog action to re-prompt for the first violation detected if user data is invalid
        if not validation_result["isValid"]:
            slots[validation_result["violatedSlot"]] = None 

            # Returns an elicitSlot dialog to request new data for the invalid slot
            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
            )

        # Gets current session attributes
        output_session_attributes = intent_request["sessionAttributes"]

        # If slot validation is successful, returns delegate dialog to Lex to choose the next course of action
        return delegate(output_session_attributes, get_slots(intent_request))

    desired_risk = get_risks(risk_level.lower())

    # Return a message with the bot's recommendation
    return close(
        intent_request["sessionAttributes"],
        "Fulfilled",
        {
            "contentType": "PlainText",
            "content": f"For a {risk_level}-risk portfolio, invest in {desired_risk}"
        },
    )

### Intents Dispatcher ###
def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    intent_name = intent_request["currentIntent"]["name"]

    # Dispatch to bot's intent handlers
    if intent_name == "recommendPortfolio":
        return recommend_portfolio(intent_request)

    raise Exception("Intent with name " + intent_name + " not supported")

### Main Handler ###
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """

    return dispatch(event)
