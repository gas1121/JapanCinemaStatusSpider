"""
module that include utility function to help crawl site
"""


def standardize_county_name(county_name):
    """
    standardize county name to full name
    """
    if county_name in ["東京都23区内", "東京都下"]:
        return "東京都"
    elif county_name == "東京":
        return county_name + "都"
    elif county_name == "北海道":
        return county_name
    elif county_name in ["大阪", "京都"]:
        return county_name + "府"
    elif "県" not in county_name:
        # "北海道" not included
        return county_name + "県"
    else:
        return county_name
